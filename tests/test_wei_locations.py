from test_base import TestWEI_Base


class TestWEI_Locations(TestWEI_Base):
    def test_workflow_replace_locations(self):
        from rpl_wei.wei_workcell_base import WEI
        from pathlib import Path
        import logging

        # workcell_config_path = Path("test_pcr_workcell.yaml")
        workflow_config_path = Path("tests/test_pcr_workflow.yaml")

        wei = WEI(
            workflow_config_path,
            log_dir=Path("logs"),
            workcell_log_level=logging.ERROR,
            workflow_log_level=logging.ERROR,
        )
        wf_id = list(wei.get_workflows().keys())[0]
        # Test that the named locations are replaced with the actual locations
        arg_before_replace = wei.get_workflows()[wf_id]["workflow"].flowdef[0].args
        self.assertEqual(arg_before_replace["source"], "sciclops.positions.exchange")
        self.assertEqual(arg_before_replace["target"], "ot2_pcr_alpha.positions.deck2")

        # Also test the compatibility of the named/actual locations
        arg_before_replace2 = wei.get_workflows()[wf_id]["workflow"].flowdef[3].args
        self.assertEqual(arg_before_replace2["source"], "sealer.positions.default")
        self.assertListEqual(
            arg_before_replace2["target"],
            [279.948, 40.849, 75.130, 598.739, 79.208, -916.456],
        )

        # Changes happen during the running of workflow
        wei.run_workflow(wf_id)

        arg_after_replace = wei.get_workflows()[wf_id]["workflow"].flowdef[0].args
        self.assertListEqual(
            arg_after_replace["source"],
            [262.550, 20.608, 119.290, 662.570, 0.0, 574.367],
        )
        self.assertListEqual(
            arg_after_replace["target"], [195.99, 60.21, 92.13, 565.41, 82.24, -65.25]
        )

        arg_after_replace2 = wei.get_workflows()[wf_id]["workflow"].flowdef[3].args
        self.assertListEqual(
            arg_after_replace2["source"],
            [231.788, -27.154, 313.011, 342.317, 0.0, 683.702],
        )
        self.assertListEqual(
            arg_after_replace2["target"],
            [279.948, 40.849, 75.130, 598.739, 79.208, -916.456],
        )
