"""Provides base classes for WEI's pytest tests"""

import time
import unittest
from pathlib import Path

import requests

import wei
from wei import ExperimentClient
from wei.core.data_classes import Workcell


class TestWEI_Base(unittest.TestCase):
    """Base class for WEI's pytest tests"""

    def __init__(self, *args, **kwargs):
        """Basic setup for WEI's pytest tests"""
        super().__init__(*args, **kwargs)
        self.root_dir = Path(__file__).resolve().parent.parent
        self.workcell = Workcell.from_yaml(
            self.root_dir / Path("tests/workcells/test_workcell.yaml")
        )
        self.server_host = self.workcell.config.server_host
        self.server_port = self.workcell.config.server_port
        self.experiment = ExperimentClient(
            self.server_host,
            self.server_port,
            "Test Experiment",
            working_dir=Path(__file__).resolve().parent,
        )
        self.url = f"http://{self.server_host}:{self.server_port}"
        self.redis_host = self.workcell.config.redis_host

        # Check to see that server is up
        start_time = time.time()
        while True:
            try:
                if requests.get(self.url + "/wc/state").status_code == 200:
                    break
            except Exception:
                pass
            time.sleep(1)
            if time.time() - start_time > 60:
                raise TimeoutError("Server did not start in 60 seconds")


class TestPackaging(TestWEI_Base):
    """Test Basic Packaging"""

    def test_wei_version(self):
        """Test WEI version"""
        assert wei.__version__


if __name__ == "__main__":
    unittest.main()
