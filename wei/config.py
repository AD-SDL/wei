"""
Handles the configuration of the engine and server.
"""

import logging
from argparse import ArgumentParser, Namespace
from pathlib import Path

import fakeredis
import yaml


class Config:
    """
    Allows for shared configuration across the application
    """

    configured = False
    workcell_file = Path("tests/test_workcell.yaml")
    workcell_name = "test_workcell"
    use_kafka = False
    reset_locations = True
    update_interval = 10.0
    server_host = "0.0.0.0"
    server_port = 8000
    redis_host = "localhost"
    redis_port = "6379"
    data_directory = Path("./tests")
    fake_redis = fakeredis.FakeStrictRedis(version=6)  # type: ignore
    log_level = 1
    test = True

    @staticmethod
    def load_config(args: Namespace) -> None:
        """Populates the config from the command line arguments"""
        Config.workcell_file = args.workcell
        with open(args.workcell, "r") as f:
            Config.workcell_name = str(yaml.safe_load(f)["name"])
        Config.redis_host = args.redis_host
        Config.redis_port = args.redis_port
        Config.update_interval = args.update_interval
        Config.reset_locations = args.reset_locations
        Config.server_host = args.server
        Config.server_port = args.port
        Config.data_directory = Path(args.data_dir)
        Config.log_level = logging.INFO
        Config.configured = True
        Config.test = False

        # Kafka Config
        Config.use_kafka = args.use_kafka

    @staticmethod
    def parse_args() -> Namespace:
        """Parse engine's command line arguments."""
        parser = ArgumentParser()
        parser.add_argument("--workcell", type=Path, help="Path to workcell file")
        parser.add_argument(
            "--redis_host",
            type=str,
            help="url (no port) for Redis server",
            default="localhost",
        )
        parser.add_argument(
            "--redis_port",
            type=int,
            help="port for Redis server",
            default=6379,
        )
        parser.add_argument(
            "--use_kafka",
            type=bool,
            help="Whether or not to log events to kafka",
            default=False,
        )
        parser.add_argument(
            "--server",
            type=str,
            help="url (no port) for the WEI server",
            default="0.0.0.0",
        )
        parser.add_argument(
            "--port",
            type=int,
            help="port for the WEI server",
            default=8000,
        )
        parser.add_argument(
            "--reset_locations",
            type=bool,
            help="Reset locations on startup",
            default=True,
        )
        parser.add_argument(
            "--update_interval",
            type=float,
            help="How long the engine waits between updates",
            default=10.0,
        )
        parser.add_argument(
            "--data_dir",
            type=Path,
            help="The directory to store logs in",
            default=Path.home() / ".wei",
        )
        return parser.parse_args()
