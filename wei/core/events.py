"""Contains the Events class for logging experiment steps"""

import traceback
from typing import Any

import requests

from wei.config import Config
from wei.core.loggers import Logger
from wei.core.state_manager import StateManager
from wei.types import Event

state_manager = StateManager()


def send_event(event: Event) -> Any:
    """Sends an event to the server to be logged"""

    event.workcell_id = getattr(Config, "workcell_id", None)
    url = f"http://{Config.server_host}:{Config.server_port}/events/"
    response = requests.post(
        url,
        json=event.model_dump(mode="json"),
    )
    if response.ok:
        return response.json()
    else:
        response.raise_for_status()


class EventHandler:
    """Registers Events during the Experiment execution both in a logfile and on Kafka"""

    kafka_producer = None
    kafka_topic = None

    @classmethod
    def initialize_diaspora(cls) -> None:
        """Initializes the Kafka producer and creates the topic if it doesn't exist already"""
        if Config.use_diaspora:
            try:
                from diaspora_event_sdk import Client, KafkaProducer, block_until_ready

                assert block_until_ready()

                def str_to_bytes(s):
                    return bytes(s, "utf-8")

                cls.kafka_producer = KafkaProducer(key_serializer=str_to_bytes)
                cls.kafka_topic = Config.kafka_topic
                print(f"Creating Diaspora topic: {cls.kafka_topic}")
                c = Client()
                assert c.register_topic(cls.kafka_topic)["status"] in [
                    "success",
                    "no-op",
                ]
            except Exception as e:
                print(e)
                print("Failed to connect to Diaspora or create topic.")
                cls.kafka_producer = None
                cls.kafka_topic = None
        else:
            cls.kafka_producer = None
            cls.kafka_topic = None

    @classmethod
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
            Logger.get_experiment_logger(event.experiment_id).info(
                event.model_dump_json()
            )
        Logger.get_workcell_logger(event.workcell_id).info(event.model_dump_json())

        if Config.use_diaspora:
            cls.log_event_diaspora(event=event)

    @classmethod
    def log_event_diaspora(cls, event: Event, retry_count=3) -> None:
        """Logs an event to diaspora"""

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
                print(f"Failed to log event to diaspora: {str(e)}")
                cls.log_event_diaspora(event, retry_count=retry_count - 1)
        else:
            cls.initialize_diaspora()
            cls.log_event_diaspora(event, retry_count=retry_count - 1)
