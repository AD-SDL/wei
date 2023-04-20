from pathlib import Path
from devtools import debug


from test_base import TestWEI_Base


def silent_callback(step, **kwargs):
    print(step)


class Test_Workcell_Base(TestWEI_Base):
    def test_workcell_property(self):
        from rpl_wei.core.wei_workcell_base import WEI

        workflow_config_path = Path("tests/test_pcr_workflow.yaml")
        wei = WEI(wf_config=workflow_config_path)

        workcell = wei.workcell

        debug(workcell)
        assert workcell is not None

    def test_payload(self):
        from rpl_wei.core.wei_workcell_base import WEI

        workflow_config_path = Path("tests/test_pcr_workflow.yaml")
        wei = WEI(wf_config=workflow_config_path)

        payload = {"thermocyle_time": 10, "thermocyle_temp": 175}

        run_info = wei.run_workflow(payload=payload, callbacks=[silent_callback])

        assert run_info["payload"] == payload
