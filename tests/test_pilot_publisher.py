import logging
from pathlib import Path

from test_base import TestWEI_Base


class TestPilotPublisher(TestWEI_Base):
    def test_publish(self):
        from rpl_wei.wei_workcell_base import WEI

        workflow_config_path = Path("tests/test_pcr_workflow.yaml")
        wei = WEI(
            wf_config=workflow_config_path,
            workcell_log_level=logging.ERROR,
            workflow_log_level=logging.ERROR,
        )

        publish_status = wei.run_workflow(publish=True)

        assert publish_status
