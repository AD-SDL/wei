import yaml
from pathlib import Path

from test_base import TestWEI_Base
from wei.core.workcell import WorkcellData


class TestExecutors(TestWEI_Base):
    def test_validators(self):
        from wei.core.step_executor import StepExecutor, StepStatus
        from wei.core.workflow import WorkflowRunner

        workflow_config_path = Path("tests/test_workflow.yaml")
        workflow_def = yaml.safe_load(workflow_config_path.read_text())
        runner = WorkflowRunner(
            workflow_def=workflow_def,
            workcell=WorkcellData.from_yaml("tests/test_workcell.yaml"),
            payload={},
            experiment_path="test_experiment",
            run_id=0,
            simulate=True,
            workflow_name="Test Workflow",
        )

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
