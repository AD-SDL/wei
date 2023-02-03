import logging
from pathlib import Path

from test_base import TestWEI_Base


class TestDCValidation(TestWEI_Base):
    def test_dataclass_validation(self):
        from rpl_wei.wei_workcell_base import WEI

        workflow_config_path = Path("tests/test_pcr_workflow.yaml")
        wei = WEI(
            wf_config=workflow_config_path,
            workcell_log_level=logging.ERROR,
            workflow_log_level=logging.ERROR,
        )

        wf = wei.get_workflow()
        print(f"{wf.flowdef=}")
