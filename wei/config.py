"""
Handles the configuration of the engine and server.
"""

import logging
from argparse import ArgumentParser, Namespace
from pathlib import Path

# import os
# from dotenv import load_dotenv


class Config:
    """
    Allows for shared configuration across the application
    """

    configured = False
    workcell_file = None
    redis_host = None
    redis_server = None
    kafka_server = None
    reset_locations = None
    update_interval = None
    server_host = None
    server_port = None
    redis_host = None
    redis_port = None
    data_directory = None
    experiment_directory = None

    @staticmethod
    def load_config(args: Namespace):
        # load_dotenv()
        # WORKCELL_FILE = os.environ.get("WORKCELL_FILE", None)
        Config.workcell_file = args.workcell
        Config.redis_host = args.redis_host
        Config.redis_port = args.redis_port
        Config.update_interval = args.update_interval
        Config.reset_locations = args.reset_locations
        Config.server_host = args.server
        Config.server_port = args.port
        Config.data_directory = Path(args.data_dir)
        Config.log_level = logging.INFO
        Config.configured = True


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
        "--kafka_server",
        type=str,
        help="url (no port) for Redis server",
        default="ec2-54-160-200-147.compute-1.amazonaws.com:9092",
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
        default=1.0,
    )
    parser.add_argument(
        "--data_dir",
        type=Path,
        help="The directory to store logs in",
        default=Path.home() / ".wei",
    )
    return parser.parse_args()


if not Config.configured:
    args = parse_args()
    Config.load_config(args)
