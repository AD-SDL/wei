"""Handles scheduling workflows and executing steps on the workcell."""

import multiprocessing as mpr
from datetime import datetime

from wei.config import Config
from wei.core.data_classes import WorkflowStatus
from wei.core.events import Events
from wei.core.location import reserve_source_and_target
from wei.core.module import reserve_module
from wei.core.state_manager import StateManager
from wei.core.step import check_step, run_step
from wei.core.workcell import find_step_module

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
                    wf_run.status = WorkflowStatus.QUEUED
                    print(
                        f"Processed new workflow: {wf_run.name} with run_id: {run_id}"
                    )
                    Events(
                        Config.server_host, Config.server_port, wf_run.experiment_id
                    ).log_wf_queued(wf_run.name, run_id)
                    state_manager.set_workflow_run(wf_run)
                elif wf_run.status == WorkflowStatus.QUEUED:
                    step = wf_run.steps[wf_run.step_index]
                    if check_step(wf_run.experiment_id, run_id, step):
                        module = find_step_module(
                            state_manager.get_workcell(), step.module
                        )
                        reserve_module(module, wf_run.run_id)
                        reserve_source_and_target(wf_run)
                        Events(
                            Config.server_host, Config.server_port, wf_run.experiment_id
                        ).log_wf_start(wf_run.name, run_id)
                        wf_run.status = WorkflowStatus.RUNNING
                        print(
                            f"Starting step {wf_run.name}.{step.name} for run: {run_id}"
                        )
                        if wf_run.step_index == 0:
                            wf_run.start_time = datetime.now()
                        wf_run.hist["run_dir"] = str(wf_run.run_dir)
                        state_manager.set_workflow_run(wf_run)
                        step_process = mpr.Process(
                            target=run_step,
                            args=(wf_run, module),
                        )
                        step_process.start()


class SequentialScheduler:
    """Handles scheduling workflow steps on the workcell.
    Runs a single workflow at a time, either to completion or failure.
    """

    current_wf_run_id = None

    def run_iteration(self) -> None:
        """
        Runs a single iteration of the scheduler, checking each workflow to see if it is able to run.
        If a workflow is able to run, it is started in a separate process.
        Workflows are processed in the order they are received, so older workflows have priority.
        Only a single Workflow is allowed to run on the workcell at a time.
        """
        with state_manager.state_lock():
            if self.current_wf_run_id is not None:
                wf_run = state_manager.get_workflow_run(self.current_wf_run_id)
                if (
                    wf_run.status == WorkflowStatus.FAILED
                    or wf_run.status == WorkflowStatus.COMPLETED
                ):
                    self.current_wf_run_id = None
            # * Update all queued workflows
            for run_id, wf_run in state_manager.get_all_workflow_runs().items():
                if wf_run.status == WorkflowStatus.NEW:
                    wf_run.status = WorkflowStatus.QUEUED
                    print(
                        f"Processed new workflow: {wf_run.name} with run_id: {run_id}"
                    )
                    Events(
                        Config.server_host, Config.server_port, wf_run.experiment_id
                    ).log_wf_queued(wf_run.name, run_id)
                    state_manager.set_workflow_run(wf_run)
                elif wf_run.status == WorkflowStatus.QUEUED:
                    step = wf_run.steps[wf_run.step_index]
                    if check_step(wf_run.experiment_id, run_id, step) and (
                        self.current_wf_run_id is None
                        or self.current_wf_run_id == wf_run.run_id
                    ):
                        self.current_workflow_run_id = wf_run.run_id
                        module = find_step_module(
                            state_manager.get_workcell(), step.module
                        )
                        reserve_module(module, wf_run.run_id)
                        reserve_source_and_target(wf_run)
                        Events(
                            Config.server_host, Config.server_port, wf_run.experiment_id
                        ).log_wf_start(wf_run.name, run_id)
                        wf_run.status = WorkflowStatus.RUNNING
                        print(
                            f"Starting step {wf_run.name}.{step.name} for run: {run_id}"
                        )
                        wf_run.start_time = datetime.now()
                        wf_run.hist["run_dir"] = str(wf_run.run_dir)
                        state_manager.set_workflow_run(wf_run)
                        step_process = mpr.Process(
                            target=run_step,
                            args=(wf_run, module),
                        )
                        step_process.start()
