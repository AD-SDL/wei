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
        arg_before_replace = workflow_def["flowdef"][1]["args"]
        self.assertEqual(arg_before_replace["source"], "webcam.pos")
        self.assertEqual(arg_before_replace["target"], "webcam.pos")


        # Changes happen during the creation of workflow runner
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

        arg_after_replace = workflow.flowdef[1].args
        self.assertListEqual(
            arg_after_replace["source"],
            [0, 0, 0, 0, 0, 0],
        )
        self.assertListEqual(
            arg_after_replace["target"],
            [0, 0, 0, 0, 0, 0],
        )
