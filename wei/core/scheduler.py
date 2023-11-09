"""Handles scheduling workflows and executing steps on the workcell."""

import multiprocessing as mpr

from wei.core.data_classes import WorkflowStatus
from wei.core.experiment import get_experiment_event_server
from wei.core.location import update_source_and_target
from wei.core.state_manager import StateManager
from wei.core.workcell import find_step_module
from wei.core.workflow import check_step, run_step

state_manager = StateManager()


class Scheduler:
    """Handles scheduling workflow steps on the workcell."""

    def run_iteration(self) -> None:
        """
        Runs a single iteration of the scheduler, checking each workflow to see if it is able to run.
        If a workflow is able to run, it is started in a separate process.
        Workflows are processed in the order they are received, so older workflows have priority.
        """
        with state_manager.state_lock():
            # * Update all queued workflows
            for run_id, wf_run in state_manager.get_all_workflow_runs().items():
                if wf_run.status == WorkflowStatus.NEW:
                    get_experiment_event_server(wf_run.experiment_id).log_wf_start(
                        wf_run.name, run_id
                    )
                    update_source_and_target(wf_run)
                    wf_run.status = WorkflowStatus.QUEUED
                    print(
                        f"Processed new workflow: {wf_run.name} with run_id: {run_id}"
                    )
                    state_manager.set_workflow_run(wf_run)
                elif wf_run.status == WorkflowStatus.QUEUED:
                    step = wf_run.steps[wf_run.step_index]
                    if check_step(wf_run.experiment_id, run_id, step):
                        module = find_step_module(
                            state_manager.get_workcell(), step.module
                        )
                        step_process = mpr.Process(
                            target=run_step,
                            args=(wf_run, module),
                        )
                        step_process.start()
                        wf_run.status = WorkflowStatus.RUNNING
                        print(
                            f"Starting step {wf_run.name}.{step.name} for run: {run_id}"
                        )
                        state_manager.set_workflow_run(wf_run)
