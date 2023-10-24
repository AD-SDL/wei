"""
Scheduler Class and associated helpers and data
"""

import multiprocessing as mpr
import time
from argparse import ArgumentParser, Namespace
from multiprocessing.connection import Connection
from pathlib import Path
from typing import Any, Tuple, Union

from wei.core.data_classes import (
    Location,
    Module,
    ModuleStatus,
    Step,
    WorkcellData,
    WorkflowStatus,
)
from wei.core.events import Events
from wei.core.interface import Interface_Map
from wei.core.loggers import WEI_Logger
from wei.core.step_executor import StepExecutor
from wei.state_manager import StateManager


def init_logger(
    experiment_path: Union[str, Path], workflow_name: Any, run_id: Any
) -> Tuple[WEI_Logger, Path]:
    """Initialize a logger for a workflow run."""
    log_dir = Path(experiment_path) / "wei_runs" / (workflow_name + "_" + str(run_id))
    result_dir = log_dir / "results"
    log_dir.mkdir(parents=True, exist_ok=True)
    result_dir.mkdir(parents=True, exist_ok=True)
    logger = WEI_Logger.get_logger("runLogger", log_dir=log_dir)
    return logger, log_dir


def find_module(workcell: WorkcellData, module_name: str) -> Module:
    """Find a module in a workcell by name."""
    for module in workcell.modules:
        if module.name == module_name:
            return module
    raise Exception("Module not found: " + module_name)


def check_step(
    exp_id, run_id, step: dict, locations: dict, state: StateManager
) -> bool:
    """Check if a step is valid."""
    print(step)
    if "target" in locations:
        location = state.get_location(locations["target"])
        if not (location.labware_id == "Empty") or not (
            location.run_id == str(run_id))
        :
            return False

    if "source" in locations:
        location = state.get_location(locations["source"])
        if not (location.labware_id == str(exp_id)):
            return False
    module_data = state.get_module(step["module"])
    if not ("BUSY" in module_data.state) and not (
        (len(module_data.queue) > 0 and module_data.queue[0] == str(run_id))
    ):
        return False
    return True


def run_step(
    exp_path: Union[str, Path],
    wf_name: Any,
    run_id: Any,
    step: Step,
    locations: dict,
    module: Module,
    pipe: Connection,
    executor: StepExecutor,
) -> None:
    """Runs a single Step from a given workflow on a specified Module."""
    logger, log_dir = init_logger(exp_path, wf_name, run_id)
    action_response, action_msg, action_log = executor.execute_step(
        step, module, logger=logger
    )
    pipe.send(
        {
            "step_response": {
                "action_response": str(action_response),
                "action_msg": action_msg,
                "action_log": action_log,
            },
            "step": step,
            "locations": locations,
            "log_dir": log_dir,
        }
    )


def parse_args() -> Namespace:
    """Parse command line arguments."""
    parser = ArgumentParser()
    parser.add_argument("--workcell", type=Path, help="Path to workcell file")
    parser.add_argument(
        "--redis_host",
        type=str,
        help="url (no port) for Redis server",
        default="localhost",
    )
    parser.add_argument(
        "--kafka_server",
        type=str,
        help="url (no port) for Redis server",
        default="ec2-54-160-200-147.compute-1.amazonaws.com:9092",
    )
    parser.add_argument(
        "--server",
        type=str,
        help="url (no port) for log server",
        default="localhost",
    )
    parser.add_argument(
        "--reset_locations",
        type=bool,
        help="Reset locations on startup",
        default=True,
    )
    parser.add_argument(
        "--update_interval",
        type=float,
        help="Time between state updates",
        default=1.0,
    )
    return parser.parse_args()


class Scheduler:
    """
    Handles scheduling workflows and executing steps on the workcell.
    Pops incoming workflows off a redis-based queue (a LIST) and executes them.
    """

    def __init__(self):
        """Initialize the scheduler."""
        self.events = {}
        self.executor = StepExecutor()
        self.processes = {}
        self.state = None
        self.kafka_server = ""
        self.log_server = ""

    def run(self, args: Namespace):  # noqa
        """Run the scheduler, popping incoming workflows queued by the server and executing them."""
        self.events = {}
        self.executor = StepExecutor()
        self.processes = {}
        self.workcell = WorkcellData.from_yaml(args.workcell)
        self.state = StateManager(
            workcell_name=self.workcell.name,
            redis_host=args.redis_host,
            redis_port=6379,
        )
        self.state.clear_state(reset_locations=args.reset_locations)
        self.kafka_server = args.kafka_server
        self.log_server = args.server
        self.state.clear_state(reset_locations=args.reset_locations)
        with self.state.state_lock():
            self.state.set_workcell(self.workcell)
            for module in self.workcell.modules:
                if not module.active:
                    continue
                module.state = ModuleStatus.INIT
                self.state.set_module(module.name, module)
            for location in self.workcell.locations:
                    self.state.set_location(
                        location.name,
                        Location(
                            name=location.name,
                            coordinates=location.coordinates,
                            
                        ),
                    )
        print("Starting Process")
        while True:
            with self.state.state_lock():  # * Lock the state for the duration of the update loop
                self.workcell = self.state.get_workcell()
                # Update Module State
                for module_name, module in self.state.get_all_modules().items():
                    if module.active:
                        self.state.set_module(
                            module_name, self.update_module_state(module)
                        )
                # * Update all queued workflows
                for run_id, wf in self.state.get_all_workflow_runs().items():
                    self.state.update_workflow_run(
                        run_id, self.update_queued_workflow, run_id
                    )
            cleanup_ids = []
            for run_id, process in self.processes.items():
                if not process["process"].is_alive():
                    process["process"].close()
                    cleanup_ids.append(run_id)
            for run_id in cleanup_ids:
                del self.processes[run_id]
            time.sleep(args.update_interval)

    def update_module_state(self, module: Module) -> Module:
        """Initialize a module."""
        module_name = module.name
        if module.interface in Interface_Map.function:
            try:
                interface = Interface_Map.function[module.interface]
                state = interface.get_state(module.config)
                if isinstance(state, dict):
                    state = state["State"]

                if not (state == ""):
                    if module.state == ModuleStatus.INIT:
                        print("Module Found: " + str(module_name))
                    module.state = ModuleStatus(state)
                else:
                    module.state = ModuleStatus.UNKNOWN
            except Exception as e:  # noqa
                if module.state == ModuleStatus.INIT:
                    print(e)
                    print("Can't Find Module: " + str(module_name))
        else:
            if self.state.get_module(module_name).state == ModuleStatus.INIT:
                print("No Module Interface for Module", str(module_name))
            pass
        return module

    def update_queued_workflow(self, wf: dict, run_id: str) -> None:
        """
        Updates state based on the given workflow and prior state.
        """
        if wf.status == WorkflowStatus.NEW:
            exp_data = Path(wf.experiment_path).name.split("_id_")
            exp_id = exp_data[-1]
            wf.experiment_id = exp_id
            exp_name = exp_data[0]
            self.events[run_id] = Events(
                self.log_server,
                "8000",
                exp_name,
                exp_id,
                self.kafka_server,
                wf.experiment_path,
            )
            self.events[run_id].log_wf_start(wf.name, run_id)
            self.update_source_and_target(wf, run_id)
            wf.status = WorkflowStatus.QUEUED
            print(f"Processed new workflow: {wf.name} with run_id: {run_id}")
        elif wf.status == WorkflowStatus.QUEUED:
            step_index = wf.step_index
            step = wf.flowdef[step_index]["step"]
            locations = wf.flowdef[step_index]["locations"]
            exp_id = Path(wf.experiment_path).name.split("_id_")[-1]
            if check_step(exp_id, run_id, step, locations, self.state):
                send_conn, rec_conn = mpr.Pipe()
                module = find_module(self.workcell, step["module"])
                step_process = mpr.Process(
                    target=run_step,
                    args=(
                        wf.experiment_path,
                        wf.name,
                        run_id,
                        Step(**step),
                        locations,
                        module,
                        send_conn,
                        self.executor,
                    ),
                )
                step_process.start()
                self.processes[run_id] = {
                    "process": step_process,
                    "pipe": rec_conn,
                }
                wf.status = WorkflowStatus.RUNNING
                print(f"Starting workflow: {wf.name} with run_id: {run_id}")
        elif wf.status == WorkflowStatus.RUNNING:
            if run_id in self.processes and self.processes[run_id]["pipe"].poll():
                print(f"Checking response from {wf.name} with run_id: {run_id}")
                try:
                    response = self.processes[run_id]["pipe"].recv()
                except Exception as e:
                    # TODO: better error handling
                    print(f"Error: {str(e)}")
                    wf.status = WorkflowStatus.FAILED
                    wf.hist[step.name] = str(e)
                    return wf
                print(f"Finished workflow: {wf.name} with run_id: {run_id}")
                print(response)
                locations = response["locations"]
                step = response["step"]
                wf.hist[step.name] = response["step_response"]
                step_index = wf.step_index
                self.processes[run_id]["process"].terminate()
                if step_index + 1 == len(wf.flowdef):
                    self.events[run_id].log_wf_end(wf.name, run_id)
                    del self.events[run_id]
                    wf.status = WorkflowStatus.COMPLETED
                    wf.step_index += 1
                    self.update_source_and_target(wf, run_id)
                    wf.hist["run_dir"] = str(response["log_dir"])
                else:
                    wf.status = WorkflowStatus.QUEUED
                    wf.step_index += 1
                    self.update_source_and_target(wf, run_id)
        return wf

    def update_source_and_target(self, wf, run_id: str) -> None:
        """Update the source and target location and module of a workflow."""
        step_index = wf.step_index
        flowdef = wf.flowdef

        # Define some helper functions to update the "queue" properties of modules and locations
        def remove_element_from_queue(object, element):
            try:
                object.queue.remove(element)
            except ValueError:
                pass
            return object

        def append_element_to_queue(object, element):
            object.queue.append(element)
            return object

        def update_location_state(object, element):
            object.state = element
            return object

        if step_index < len(wf.flowdef):
            if "target" in flowdef[step_index]["locations"]:
                self.state.update_location(
                    flowdef[step_index]["locations"]["target"],
                    append_element_to_queue,
                    run_id,
                )
            self.state.update_module(
                flowdef[step_index]["step"]["module"], append_element_to_queue, run_id
            )

        if step_index > 0:
            self.state.update_module(
                flowdef[step_index - 1]["step"]["module"],
                remove_element_from_queue,
                run_id,
            )
            if "source" in flowdef[step_index - 1]["locations"]:
                self.state.update_location(
                    flowdef[step_index - 1]["locations"]["source"],
                    update_location_state,
                    "Empty",
                )
            if "target" in flowdef[step_index - 1]["locations"]:
                if not ("trash" in flowdef[step_index - 1]["locations"]["target"]):
                    self.state.update_location(
                        flowdef[step_index - 1]["locations"]["target"],
                        update_location_state,
                        wf.experiment_id,
                    )
                self.state.update_location(
                    flowdef[step_index - 1]["locations"]["target"],
                    remove_element_from_queue,
                    run_id,
                )


if __name__ == "__main__":
    args = parse_args()
    scheduler = Scheduler()
    scheduler.run(args)
