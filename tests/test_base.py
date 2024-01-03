"""Provides base classes for WEI's pytest tests"""
import unittest
from pathlib import Path

import wei
from wei.core.data_classes import WorkcellData


class TestWEI_Base(unittest.TestCase):
    """Base class for WEI's pytest tests"""

    def __init__(self, *args, **kwargs):
        """Basic setup for WEI's pytest tests"""
        super().__init__(*args, **kwargs)
        self.root_dir = Path(__file__).resolve().parent.parent
        self.workcell = WorkcellData.from_yaml(
            self.root_dir / Path("workcell_defs/test_workcell.yaml")
        )
        self.server_host = self.workcell.config.server_host
        self.server_port = self.workcell.config.server_port
        self.url = f"http://{self.server_host}:{self.server_port}"
        self.redis_host = self.workcell.config.redis_host


class TestPackaging(TestWEI_Base):
    """Test Basic Packaging"""

    def test_wei_version(self):
        """Test WEI version"""
        assert wei.__version__


if __name__ == "__main__":
    unittest.main()
