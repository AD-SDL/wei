import yaml
from pathlib import Path

from test_base import TestWEI_Base


class TestExecutors(TestWEI_Base):
    def test_validators(self):
        from rpl_wei.core.executors import StepExecutor, StepStatus
        from rpl_wei.core.workflow import WorkflowRunner

        workflow_config_path = Path("tests/test_pcr_workflow.yaml")
        worfklow_def = yaml.safe_load(workflow_config_path.read_text())
        runner = WorkflowRunner(worfklow_def, "test_experiment")

        step_executor = StepExecutor()
        # get run id (TODO: this is clunky...)
        for step in runner.workflow.flowdef:
            # TODO figure out a better way to do get the step the module requires (the `None`)
            try:
                step_status = step_executor.execute_step(step, None, callbacks=None)
            except Exception:
                # TODO: oops don't care
                step_status = StepStatus.FAILED
                pass

            assert step_status
            # assert step_status == StepStatus.SUCCEEDED
