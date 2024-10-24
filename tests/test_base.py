"""Provides base classes for WEI's pytest tests"""

import unittest
from pathlib import Path

import wei
from wei import ExperimentClient
from wei.types import Workcell
from wei.types.experiment_types import CampaignDesign, ExperimentDesign


class TestWEI_Base(unittest.TestCase):
    """Base class for WEI's pytest tests"""

    experiment = ExperimentDesign(
        experiment_name="Test_Experiment",
        experiment_description="An experiment for automated testing",
        email_addresses=[],
    )
    campaign = CampaignDesign(
        campaign_name="Test_Campaign",
        campaign_description="A campaign for automated testing",
    )
    experiment_client = None

    def __init__(self, *args, **kwargs):
        """Basic setup for WEI's pytest tests"""
        super().__init__(*args, **kwargs)
        self.root_dir = Path(__file__).resolve().parent.parent
        self.workcell = Workcell.from_yaml(
            self.root_dir / Path("tests/workcells/test_workcell.yaml")
        )
        self.server_host = self.workcell.config.server_host
        self.server_port = self.workcell.config.server_port
        if not self.experiment_client:
            self.experiment_client = ExperimentClient(
                server_host=self.server_host,
                server_port=self.server_port,
                experiment=TestWEI_Base.experiment,
                campaign=TestWEI_Base.campaign,
                working_dir=Path(__file__).resolve().parent,
            )
            TestWEI_Base.experiment = self.experiment_client.experiment
            TestWEI_Base.campaign = self.experiment_client.campaign
            TestWEI_Base.experiment_client = self.experiment_client
        self.url = f"http://{self.server_host}:{self.server_port}"
        self.redis_host = self.workcell.config.redis_host

    def __del__(self):
        """Basic cleanup for WEI's pytest tests"""
        if self.experiment_client:
            self.experiment_client.log_experiment_end()


class TestPackaging(TestWEI_Base):
    """Test Basic Packaging"""

    def test_wei_version(self):
        """Test WEI version"""
        assert wei.__version__


if __name__ == "__main__":
    unittest.main()
