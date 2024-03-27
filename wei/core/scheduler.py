"""Handles scheduling workflows and executing steps on the workcell."""

import multiprocessing as mpr
from datetime import datetime

from wei.core.events import send_event
from wei.core.location import reserve_source_and_target
from wei.core.loggers import get_workflow_run_dir
from wei.core.module import reserve_module
from wei.core.state_manager import StateManager
from wei.core.step import check_step, run_step
from wei.core.workcell import find_step_module
from wei.types import WorkflowStatus
from wei.types.event_types import WorkflowQueuedEvent, WorkflowStartEvent

state_manager = StateManager()


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
        with state_manager.state_lock():
            # * Update all queued workflows
            for run_id, wf_run in state_manager.get_all_workflow_runs().items():
                if wf_run.status == WorkflowStatus.NEW:
                    wf_run.status = WorkflowStatus.QUEUED
                    print(
                        f"Processed new workflow: {wf_run.name} with run_id: {run_id}"
                    )
                    send_event(WorkflowQueuedEvent.from_wf_run(wf_run=wf_run))
                    state_manager.set_workflow_run(wf_run)
                elif wf_run.status in [WorkflowStatus.QUEUED, WorkflowStatus.WAITING]:
                    step = wf_run.steps[wf_run.step_index]
                    if check_step(wf_run.experiment_id, run_id, step):
                        module = find_step_module(
                            state_manager.get_workcell(), step.module
                        )
                        reserve_module(module, wf_run.run_id)
                        reserve_source_and_target(wf_run)
                        send_event(WorkflowStartEvent.from_wf_run(wf_run=wf_run))
                        wf_run.status = WorkflowStatus.RUNNING
                        print(
                            f"Starting step {wf_run.name}.{step.name} for run: {run_id}"
                        )
                        if wf_run.step_index == 0:
                            wf_run.start_time = datetime.now()
                        wf_run.hist["run_dir"] = str(get_workflow_run_dir(wf_run))
                        state_manager.set_workflow_run(wf_run)
                        step_process = mpr.Process(
                            target=run_step,
                            args=(wf_run, module),
                        )
                        step_process.start()
