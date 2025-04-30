"""Handles scheduling workflows and executing steps on the workcell."""

from datetime import datetime

from wei.core.events import send_event
from wei.core.state_manager import state_manager
from wei.core.step import check_step, run_step
from wei.core.workcell import find_step_module
from wei.core.workflow_admin import wf_status_change
from wei.types import WorkflowStatus
from wei.types.event_types import (
    WorkflowQueuedEvent,
    WorkflowStartEvent,
)


class Scheduler:
    """Handles scheduling workflow steps on the workcell."""

    def __init__(self, sequential: bool = False) -> None:
        """Initializes the scheduler."""
        self.sequential = sequential

    def run_iteration(self) -> None:
        """
        Runs a single iteration of the scheduler, checking each workflow to see if it is able to run.
        If a workflow is able to run, it is started in a separate process.
        Workflows are processed in the order they are received, so older workflows have priority.
        """
        with state_manager.wc_state_lock():
            # * Update all queued workflows
            for run_id, wf_run in state_manager.get_all_workflow_runs().items():
                if wf_run.status == WorkflowStatus.PAUSED:  # ***
                    continue
                elif wf_run.status == WorkflowStatus.NEW:
                    wf_run.status = WorkflowStatus.QUEUED
                    print(
                        f"Processed new workflow: {wf_run.name} with run_id: {run_id}"
                    )
                    send_event(WorkflowQueuedEvent.from_wf_run(wf_run=wf_run))
                    state_manager.set_workflow_run(wf_run)
                elif wf_run.status in [
                    WorkflowStatus.QUEUED,
                    WorkflowStatus.IN_PROGRESS,
                ]:
                    wf_status_change.clear()
                    step = wf_run.steps[wf_run.step_index]
                    if check_step(wf_run.experiment_id, run_id, step):
                        module = find_step_module(
                            state_manager.get_workcell(), step.module
                        )
                        if wf_run.status == WorkflowStatus.QUEUED:
                            send_event(WorkflowStartEvent.from_wf_run(wf_run=wf_run))
                        wf_run.status = WorkflowStatus.RUNNING
                        print(
                            f"Starting step {wf_run.name}.{step.name} for run: {run_id}"
                        )
                        if wf_run.step_index == 0:
                            wf_run.start_time = datetime.now()
                        state_manager.set_workflow_run(wf_run)
                        run_step(wf_run=wf_run, module=module)
