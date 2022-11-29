import logging
from pathlib import Path

from test_base import TestWEI_Base


class TestPilotPublisher(TestWEI_Base):
    def test_publish(self):
        from rpl_wei.wei_workcell_base import WEI

        workflow_config_path = Path("tests/test_pcr_workflow.yaml")
        wei = WEI(
            wf_configs=workflow_config_path,
            workcell_log_level=logging.ERROR,
            workflow_log_level=logging.ERROR,
        )

        run_id = list(wei.get_workflows().keys())[0]
        publish_status = wei.run_workflow(run_id, publish=True)

        assert publish_status
