import logging
from pathlib import Path

from test_base import TestWEI_Base


class TestDCValidation(TestWEI_Base):
    def test_dataclass_validation(self):
        from rpl_wei.wei_workcell_base import WEI

        workflow_config_path = Path("tests/test_pcr_workflow.yaml")
        wei = WEI(
            wf_configs=workflow_config_path,
            workcell_log_level=logging.ERROR,
            workflow_log_level=logging.ERROR,
        )

        run = list(wei.get_workflows().keys())[0]

        wf = wei.get_workflow(run)
        print(f"{wf['workflow'].flowdef=}")
