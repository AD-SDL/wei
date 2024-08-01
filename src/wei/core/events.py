"""Contains the Events class for logging experiment steps"""

import random
import time
import traceback
from typing import Any

import requests

from wei.config import Config
from wei.core.loggers import Logger
from wei.core.state_manager import state_manager
from wei.types import Event
from wei.utils import threaded_task


@threaded_task
def send_event(event: Event, retry_count=3) -> Any:
    """Sends an event to the server to be logged"""

    event.workcell_id = getattr(Config, "workcell_id", None)
    url = f"http://{Config.server_host}:{Config.server_port}/events/"
    response = requests.post(url, json=event.model_dump(mode="json"), timeout=10)
    if response.ok:
        return response.json()
    elif retry_count > 0:
        time.sleep(
            random.uniform(1, 10)
        )  # * Random retry interval to reduce retry pressure.
        return send_event(event, retry_count - 1)
    else:
        response.raise_for_status()


class EventHandler:
    """Registers Events during the Experiment execution in a logfile, in Redis, and (if `use_diaspora` is true) on Kafka"""

    kafka_producer = None
    kafka_topic = None
    kafka_init_retry = 3
    kafka_initializing = False

    @classmethod
    @threaded_task
    def initialize_diaspora(cls) -> bool:
        """Initializes the Kafka producer and creates the topic if it doesn't exist already"""
        if (
            Config.use_diaspora
            and cls.kafka_init_retry > 0
            and not cls.kafka_initializing
        ):
            cls.kafka_initializing = True
            cls.kafka_init_retry -= 1
            result = None
            try:
                from diaspora_event_sdk import Client, KafkaProducer, block_until_ready

                assert block_until_ready()

                def str_to_bytes(s):
                    return bytes(s, "utf-8")

                cls.kafka_producer = KafkaProducer(key_serializer=str_to_bytes)
                cls.kafka_topic = Config.kafka_topic
                c = Client()
                if cls.kafka_topic not in c.list_topics()["topics"]:
                    print(f"Creating Diaspora topic: {cls.kafka_topic}")
                    result = c.register_topic(cls.kafka_topic)

                    if result["status"] not in [
                        "success",
                        "no-op",
                    ]:
                        print("Failed to initialize diaspora.")
                        print(result)
                        cls.kafka_producer = None
                        cls.kafka_topic = None
                        cls.kafka_initializing = False
                        return False
                cls.kafka_initializing = False
                return True
            except Exception:
                traceback.print_exc()
                print("Failed to connect to Diaspora or create topic.")
                cls.kafka_producer = None
                cls.kafka_topic = None
                cls.kafka_initializing = False
                return False

    @classmethod
    @threaded_task
    def log_event(cls, event: Event) -> None:
        """logs an event in the proper place for the given experiment

        Parameters
        ----------
        log_value : str
            the specifically formatted value to log

        Returns
        -------
        None
        """

        if event.workcell_id is None:
            event.workcell_id = state_manager.get_workcell_id()
        if event.experiment_id is not None:
            # Log all events related to an experiment to the experiment's log file
            Logger.get_experiment_logger(event.experiment_id).info(
                event.model_dump_json()
            )
        else:
            # Log all non-experiment events to the workcell's log file
            Logger.get_workcell_logger(event.workcell_id).info(event.model_dump_json())
        if event.event_type == "WORKFLOW":
            # Log all workflow events to the workflow run's log file, in addition to the experiment log file
            Logger.get_workflow_run_logger(event.run_id).info(event.model_dump_json())

        state_manager.set_event(event)

        if Config.use_diaspora:
            cls.log_event_diaspora(event=event)

    @classmethod
    def log_event_diaspora(cls, event: Event, retry_count=3) -> None:
        """Logs an event to diaspora"""

        while cls.kafka_initializing:
            time.sleep(1)

        if cls.kafka_producer and cls.kafka_topic:
            try:
                future = cls.kafka_producer.send(
                    topic=cls.kafka_topic,
                    key=event.event_id,
                    value=event.model_dump(mode="json"),
                )
                print(future.get(timeout=10))
            except Exception as e:
                traceback.print_exc()
                print(
                    f"Failed to log event to diaspora ({str(e)}), retrying {retry_count} more time(s)"
                )
                cls.log_event_diaspora(event, retry_count=retry_count - 1)
        else:
            while cls.kafka_initializing:
                time.sleep(1)
            if cls.kafka_init_retry > 0 and cls.initialize_diaspora():
                cls.log_event_diaspora(event, retry_count=retry_count - 1)
