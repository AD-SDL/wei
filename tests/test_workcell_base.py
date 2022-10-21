from pathlib import Path
from rich.pretty import pprint

from tests.test_base import TestWEI_Base


class Test_Workcell_Base(TestWEI_Base):
    def test_workcell_property(self):
        from rpl_wei.wei_workcell_base import WEI

        workflow_config_path = Path("tests/test_pcr_workflow.yaml")
        wei = WEI(wf_configs=workflow_config_path)

        workcell = wei.workcell

        pprint(workcell)
        assert workcell is not None
