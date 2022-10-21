from pathlib import Path
import logging

from test_base import TestWEI_Base


class TestExecutors(TestWEI_Base):
    def test_validators(self):
        from rpl_wei.executors import StepExecutor, StepStatus
        from rpl_wei.wei_workcell_base import WEI

        step_executor = StepExecutor(logging)

        workflow_config_path = Path("tests/test_pcr_workflow.yaml")
        wei = WEI(wf_configs=workflow_config_path)

        # get run id (TODO: this is clunky...)
        run_id = list(wei.get_workflows().keys())[0]
        wf_dict = wei.get_workflow(run_id)
        wf = wf_dict.get("workflow")
        for step in wf.flowdef:
            # TODO figure out a better way to do get the step the module requires (the `None`)
            step_status = step_executor.execute_step(step, None, callbacks=None)

            assert step_status == StepStatus.SUCCEEDED
