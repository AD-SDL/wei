"""Contains the Events class for logging experiment steps"""

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
                cls.kafka_producer = KafkaProducer()
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
            cls.log_event_diaspora(event)

    def log_event_diaspora(self, log_value: Event) -> None:
        """Logs an event to diaspora"""

        if self.kafka_producer and self.kafka_topic:
            try:
                future = self.kafka_producer.send(
                    self.kafka_topic, log_value.model_dump(mode="json")
                )
                print(future.get(timeout=10))
            except Exception as e:
                print(f"Failed to log event to diaspora: {str(e)}")
        else:
            print("Diaspora not initialized.")
