import yaml
from test_base import TestWEI_Base


class TestWEI_Locations(TestWEI_Base):
    def test_workflow_replace_locations(self):
        from pathlib import Path

        from wei.core.workflow import WorkflowRunner
        from wei.core.workcell import Workcell

        workcell_config_path = Path("tests/test_workcell.yaml")
        workcell_def = yaml.safe_load(workcell_config_path.read_text())
        workcell = Workcell(workcell_def)

        workflow_config_path = Path("tests/test_workflow.yaml")
        worfklow_def = yaml.safe_load(workflow_config_path.read_text())
        runner = WorkflowRunner(worfklow_def, "test_experiment")
        workflow = runner.workflow

        # Test that the named locations are replaced with the actual locations
        print(workflow)
        print("testing")
        arg_before_replace = workflow.flowdef[1].args
        self.assertEqual(arg_before_replace["source"], "camera.pos")
        self.assertEqual(arg_before_replace["target"], "camera.pos")

        # Also test the compatibility of the named/actual locations

        # Changes happen during the running of workflow
        runner.run_flow(workcell)

        arg_after_replace = workflow.flowdef[1].args
        self.assertListEqual(
            arg_after_replace["source"],
            [0, 0, 0, 0, 0, 0],
        )
        self.assertListEqual(
            arg_after_replace["target"],
            [0, 0, 0, 0, 0, 0],
        )
