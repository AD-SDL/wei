"""
Handles the configuration of the engine and server.
"""

from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Optional

from wei.core.data_classes import WorkcellData
from wei.core.state_manager import StateManager


# import os
# from dotenv import load_dotenv


class Config:
    """
    Allows for shared configuration across the application
    """

    workcell = None
    redis_host = None
    redis_server = None
    kafka_server = None
    reset_locations = None
    update_interval = None
    server_host = None
    server_port = None
    log_server = None
    log_server_port = None
    state_manager: Optional[StateManager] = None

    @staticmethod
    def load_engine_config(self, args: Namespace):
        # load_dotenv()
        # WORKCELL_FILE = os.environ.get("WORKCELL_FILE", None)
        self.workcell = WorkcellData.from_yaml(args.workcell)
        self.redis_host = args.redis_host
        self.redis_port = args.redis_port
        self.update_interval = args.update_interval
        self.reset_locations = args.reset_locations
        self.state_manager = StateManager(
            workcell_name=self.workcell.name,
            redis_host=args.redis_host,
            redis_port=args.redis_port,
        )
        self.log_server = args.log_server
        self.log_server_port = args.log_server_port

    @staticmethod
    def load_server_config(self, args: Namespace):
        self.workcell = WorkcellData.from_yaml(args.workcell)
        self.redis_host = args.redis_host
        self.redis_port = args.redis_port
        self.state_manager = StateManager(
            workcell_name=self.workcell.name,
            redis_host=args.redis_host,
            redis_port=args.redis_port,
        )


def parse_args() -> Namespace:
    """Parse engine's command line arguments."""
    parser = ArgumentParser()
    parser.add_argument(
        "--workcell", type=Path, help="Path to workcell file", required=True
    )
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
        "--kafka_server",
        type=str,
        help="url (no port) for Redis server",
        default="ec2-54-160-200-147.compute-1.amazonaws.com:9092",
    )
    parser.add_argument(
        "--server",
        type=str,
        help="url (no port) for the WEI server",
        default="localhost",
    )
    parser.add_argument(
        "--port",
        type=int,
        help="port for the WEI server",
        default=8080,
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
        default=1.0,
    )
    return parser.parse_args()
