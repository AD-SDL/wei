import yaml
from test_base import TestWEI_Base


class TestWEI_Locations(TestWEI_Base):
    def test_workflow_replace_locations(self):
        from pathlib import Path

        from rpl_wei.core.workflow import WorkflowRunner
        from rpl_wei.core.workcell import Workcell

        workcell_config_path = Path("tests/test_pcr_workcell.yaml")
        workcell_def = yaml.safe_load(workcell_config_path.read_text())
        workcell = Workcell(workcell_def)

        workflow_config_path = Path("tests/test_pcr_workflow.yaml")
        worfklow_def = yaml.safe_load(workflow_config_path.read_text())
        runner = WorkflowRunner(worfklow_def, "test_experiment")
        workflow = runner.workflow

        # Test that the named locations are replaced with the actual locations
        arg_before_replace = workflow.flowdef[1].args
        self.assertEqual(arg_before_replace["source"], "sciclops.positions.exchange")
        self.assertEqual(arg_before_replace["target"], "ot2_pcr_alpha.positions.deck2")

        # Also test the compatibility of the named/actual locations
        arg_before_replace2 = workflow.flowdef[5].args
        self.assertEqual(arg_before_replace2["source"], "sealer.positions.default")
        self.assertListEqual(
            arg_before_replace2["target"],
            [279.948, 40.849, 75.130, 598.739, 79.208, -916.456],
        )

        # Changes happen during the running of workflow
        runner.run_flow(workcell)

        arg_after_replace = workflow.flowdef[1].args
        self.assertListEqual(
            arg_after_replace["source"],
            [222.0, -38.068, 335.876, 325.434, 79.923, 995.062] 
        )
        self.assertListEqual(
            arg_after_replace["target"], [195.99, 60.21, 92.13, 565.41, 82.24, -65.25]
        )

        arg_after_replace2 = workflow.flowdef[5].args
        self.assertListEqual(
            arg_after_replace2["source"],
            [205.128, -2.814, 264.373, 365.863, 79.144, 411.553],
        )
        self.assertListEqual(
            arg_after_replace2["target"],
            [279.948, 40.849, 75.130, 598.739, 79.208, -916.456],
        )
