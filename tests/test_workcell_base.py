from pathlib import Path
from devtools import debug


from test_base import TestWEI_Base

from rpl_wei.data_classes import Payload


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

        payload = Payload(input={"name": "input-name"})

        wei.run_workflow(workflow_id=run, payload=payload, callbacks=[silent_callback])

        post_run = wei.get_workflow(run)
        post_run_payload = post_run[list(post_run.keys())[-1]]

        assert post_run_payload == payload
