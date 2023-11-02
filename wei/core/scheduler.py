"""Handles scheduling workflows and executing steps on the workcell."""

import multiprocessing as mpr

from wei.core.config import Config
from wei.core.data_classes import Experiment, WorkflowRun, WorkflowStatus
from wei.core.events import Events
from wei.core.location import update_source_and_target
from wei.core.workcell import find_step_module
from wei.core.workflow import check_step, run_step

state_manager = Config.state_manager


class Scheduler:
    def __init__(self):
        self.processes = {}
        self.events = {}

    def run_iteration(self):
        with state_manager.state_lock():
            # * Update all queued workflows
            for run_id in self.state_manager.get_all_workflow_runs():
                state_manager.update_workflow_run(
                    run_id, self.update_queued_workflow, run_id
                )
        self.cleanup_processes()

    def update_queued_workflow(self, wf_run: WorkflowRun, run_id: str) -> None:
        """
        Updates state based on the given workflow and prior state.
        """
        if wf_run.status == WorkflowStatus.NEW:
            experiment = Experiment(experiment_id=wf_run.experiment_id)
            self.events[run_id] = Events(
                Config.log_server,
                Config.log_server_port,
                experiment.experiment_id,
                wei_internal=True,
            )
            self.events[run_id].log_wf_start(wf_run.name, run_id)
            update_source_and_target(wf_run)
            wf_run.status = WorkflowStatus.QUEUED
            print(f"Processed new workflow: {wf_run.name} with run_id: {run_id}")
        elif wf_run.status == WorkflowStatus.QUEUED:
            step_index = wf_run.step_index
            step = wf_run.steps[step_index]
            if check_step(wf_run.experiment_id, run_id, step):
                send_conn, rec_conn = mpr.Pipe()
                module = find_step_module(state_manager.get_workcell(), step.module)
                step_process = mpr.Process(
                    target=run_step,
                    args=(wf_run, module, send_conn),
                )
                step_process.start()
                self.processes[run_id] = {
                    "process": step_process,
                    "pipe": rec_conn,
                }
                wf_run.status = WorkflowStatus.RUNNING
                print(f"Starting workflow: {wf_run.name} with run_id: {run_id}")
        elif wf_run.status == WorkflowStatus.RUNNING:
            if run_id in self.processes and self.processes[run_id]["pipe"].poll():
                print(f"Checking response from {wf_run.name} with run_id: {run_id}")
                try:
                    response = self.processes[run_id]["pipe"].recv()
                except Exception as e:
                    # TODO: better error handling
                    print(f"Error: {str(e)}")
                    wf_run.status = WorkflowStatus.FAILED
                    wf_run.hist[step.name] = str(e)
                    return wf_run
                print(f"Finished workflow: {wf_run.name} with run_id: {run_id}")
                print(response)
                step = response["step"]
                wf_run.hist[step.name] = response["step_response"]
                step_index = wf_run.step_index
                self.processes[run_id]["process"].terminate()
                if step_index + 1 == len(wf_run.steps):
                    self.events[run_id].log_wf_end(wf_run.name, run_id)
                    del self.events[run_id]
                    wf_run.status = WorkflowStatus.COMPLETED
                    wf_run.step_index += 1
                    update_source_and_target(wf_run)
                    wf_run.hist["run_dir"] = str(response["log_dir"])
                else:
                    wf_run.status = WorkflowStatus.QUEUED
                    wf_run.step_index += 1
                    update_source_and_target(wf_run)
        return wf_run

    def cleanup_processes(self):
        cleanup_ids = []
        for run_id, process in self.processes.items():
            if not process["process"].is_alive():
                process["process"].close()
                cleanup_ids.append(run_id)
        for run_id in cleanup_ids:
            del self.processes[run_id]
