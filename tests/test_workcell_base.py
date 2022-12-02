from pathlib import Path
from devtools import debug


from test_base import TestWEI_Base


def silent_callback(step, **kwargs):
    pass


class Test_Workcell_Base(TestWEI_Base):
    def test_workcell_property(self):
        from rpl_wei.wei_workcell_base import WEI

        workflow_config_path = Path("tests/test_pcr_workflow.yaml")
        wei = WEI(wf_configs=workflow_config_path)

        workcell = wei.workcell

        debug(workcell)
        assert workcell is not None

    def test_payload(self):
        from rpl_wei.wei_workcell_base import WEI

        workflow_config_path = Path("tests/test_pcr_workflow.yaml")
        wei = WEI(wf_configs=workflow_config_path)

        run = list(wei.get_workflows().keys())[0]

        payload = {"thermocycle_time": 10, "thermocycle_temp": 175}

        wei.run_workflow(workflow_id=run, payload=payload, callbacks=[silent_callback])

        post_run = wei.get_workflow(run)
        post_run_payload = post_run[list(post_run.keys())[-1]]

        assert post_run_payload == payload
