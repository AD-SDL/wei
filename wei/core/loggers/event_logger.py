"""Contains the EventLogger class for logging events to log files and/or Diaspora"""

from typing import Any, Dict

from wei.config import Config
from wei.core.loggers.loggers import Logger
from wei.core.state_manager import StateManager
from wei.types import Event


class EventLogger:
    """Registers Events during the Experiment execution both in a logfile and on Kafka"""

    def __init__(
        self,
        experiment_id: str,
    ) -> None:
        """Initializes an Event Logging object

        Parameters
        ----------
        experiment_id: str
            Programmatically generated experiment id, can be reused if needed

        Returns
        ----------
        None
        """
        self.experiment_id = experiment_id
        self.state_manager = StateManager()

    @classmethod
    def initialize_diaspora(cls) -> None:
        """Initializes the Kafka producer and creates the topic if it doesn't exist already"""
        if Config.use_diaspora:
            try:
                from diaspora_event_sdk import Client, KafkaProducer, block_until_ready

                assert block_until_ready()
                cls.kafka_producer = KafkaProducer()
                print("Creating Diaspora topic: %s", Config.kafka_topic)
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

    def log_event(self, log_value: Event) -> Dict[Any, Any]:
        """logs an event in the proper place for the given experiment

        Parameters
        ----------
        log_value : str
            the specifically formatted value to log

        Returns
        -------
        None
        """

        log_value.workcell_id = self.state_manager.get_workcell_id()
        logger = Logger.get_experiment_logger(self.experiment_id)
        logger.info(log_value.model_dump_json())

        if self.kafka_producer:
            try:
                future = self.kafka_producer.send(
                    self.kafka_topic, log_value.model_dump(mode="json")
                )
                print(future.get(timeout=10))
            except Exception as e:
                print(str(e))
