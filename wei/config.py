"""
Handles the configuration of the engine and server.
"""

import logging
from argparse import ArgumentParser, Namespace
from pathlib import Path

# import os
# from dotenv import load_dotenv

global config


class Config:
    """
    Allows for shared configuration across the application
    """

    workcell_file = None
    redis_host = None
    redis_server = None
    kafka_server = None
    reset_locations = None
    update_interval = None
    server_host = None
    server_port = None
    log_server = None
    log_server_port = None
    redis_host = None
    redis_port = None
    data_directory = None
    experiment_directory = None


def load_engine_config(args: Namespace):
    # load_dotenv()
    # WORKCELL_FILE = os.environ.get("WORKCELL_FILE", None)
    global config
    config = Config()
    config.workcell_file = args.workcell
    config.redis_host = args.redis_host
    config.redis_port = args.redis_port
    config.update_interval = args.update_interval
    config.reset_locations = args.reset_locations
    config.redis_host = (args.redis_host,)
    config.redis_port = (args.redis_port,)
    config.log_server = args.server
    config.log_server_port = args.server_port
    config.data_directory = Path(args.data_dir)
    config.log_level = logging.INFO


def load_server_config(args: Namespace):
    global config
    config = Config()
    config.workcell_file = args.workcell
    config.server_host = args.server
    config.server_port = args.port
    config.redis_host = args.redis_host
    config.redis_port = args.redis_port
    config.redis_host = (args.redis_host,)
    config.redis_port = (args.redis_port,)
    config.data_directory = Path(args.data_dir)


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
    parser.add_argument(
        "--data_dir",
        type=Path,
        help="The directory to store logs in",
        default=Path.home() / ".wei",
    )
    return parser.parse_args()
