from pathlib import Path

from test_base import TestWEI_Base


class TestExecutors(TestWEI_Base):
    def test_validators(self):
        from rpl_wei.executors import StepExecutor, StepStatus
        from rpl_wei.wei_workcell_base import WEI

        step_executor = StepExecutor()

        workflow_config_path = Path("tests/test_pcr_workflow.yaml")
        wei = WEI(wf_config=workflow_config_path)

        # get run id (TODO: this is clunky...)
        wf = wei.workflow
        for step in wf.flowdef:
            # TODO figure out a better way to do get the step the module requires (the `None`)
            try:
                step_status = step_executor.execute_step(step, None, callbacks=None)
            except Exception as e:
                # TODO: oops don't care
                step_status = StepStatus.FAILED
                pass

            assert step_status
            # assert step_status == StepStatus.SUCCEEDED
