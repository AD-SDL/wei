"""Tests for WEI Workcell functionality"""

from pathlib import Path

from devtools import debug
from test_base import TestWEI_Base

# from wei.core.data_classes import WorkcellData


class Test_Workcell_Base(TestWEI_Base):
    """Tests for WEI Workcell functionality"""

    def test_workcell_property(self):
        """Test that WEI properly loads a workcell"""
        from wei.core.workcell import WorkcellData

        workcell_config_path = Path("tests/test_workcell.yaml")
        workcell = WorkcellData.from_yaml(workcell_config_path)

        debug(workcell)
        assert workcell is not None

    def test_payload(self):
        """Test that WEI properly replaces Workflow payloads"""
        # from wei.core.workcell import Workcell
        # from wei.core.workflow import WorkflowRunner

        # workcell_config_path = Path("tests/test_workcell.yaml")
        # workcell_def = yaml.safe_load(workcell_config_path.read_text())
        # workcell = Workcell(workcell_def)
        # workflow_config_path = Path("tests/test_workflow.yaml")
        # workflow_def = yaml.safe_load(workflow_config_path.read_text())
        # runner = WorkflowRunner(
        #     workflow_def=workflow_def,
        #     workcell=WorkcellData.from_yaml("tests/test_workcell.yaml"),
        #     payload={},
        #     experiment_path="test_experiment",
        #     run_id=0,
        #     simulate=True,
        #     workflow_name="Test Workflow",
        # )

        payload = {}

        # run_info = runner.run_flow(workcell, payload=payload, simulate=True)
        # TODO: Fix all testing to use run_step
        assert payload == payload
