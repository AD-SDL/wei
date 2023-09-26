import yaml
from test_base import TestWEI_Base

from wei.core.data_classes import WorkcellData


class TestWEI_Locations(TestWEI_Base):
    def test_workflow_replace_locations(self):
        from pathlib import Path

        from wei.core.workcell import Workcell
        from wei.core.workflow import WorkflowRunner

        workcell_config_path = Path("tests/test_workcell.yaml")
        workcell_def = yaml.safe_load(workcell_config_path.read_text())
        workcell = Workcell(workcell_def)

        workflow_config_path = Path("tests/test_workflow.yaml")
        workflow_def = yaml.safe_load(workflow_config_path.read_text())
        runner = WorkflowRunner(
            workflow_def=workflow_def,
            workcell=WorkcellData.from_yaml("tests/test_workcell.yaml"),
            payload={},
            experiment_path="test_experiment",
            run_id=0,
            simulate=True,
            workflow_name="Test Workflow",
        )
        workflow = runner.workflow

        # Test that the named locations are replaced with the actual locations
        # arg_before_replace = workflow.flowdef[1].args
        # self.assertEqual(arg_before_replace["source"], "camera.pos")
        # self.assertEqual(arg_before_replace["target"], "camera.pos")

        # Also test the compatibility of the named/actual locations

        # Changes happen during the running of workflow
        runner.run_flow(workcell, simulate=True)

        arg_after_replace = workflow.flowdef[1].args
        self.assertListEqual(
            arg_after_replace["source"],
            [0, 0, 0, 0, 0, 0],
        )
        self.assertListEqual(
            arg_after_replace["target"],
            [0, 0, 0, 0, 0, 0],
        )
