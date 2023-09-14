import json
import multiprocessing as mpr
import time
from argparse import ArgumentParser
from pathlib import Path

import redis
import yaml

from wei.core.data_classes import Step
from wei.core.data_classes import Workcell as WorkcellData
from wei.core.events import Events
from wei.core.loggers import WEI_Logger
from wei.core.step_executor import Executor_Map, StepExecutor
from wei.core.workflow import WorkflowRunner


def init_logger(experiment_path, workflow_name, run_id):
    log_dir = Path(experiment_path) / "wei_runs" / (workflow_name + "_" + str(run_id))
    result_dir = log_dir / "results"
    log_dir.mkdir(parents=True, exist_ok=True)
    result_dir.mkdir(parents=True, exist_ok=True)
    logger = WEI_Logger.get_logger("runLogger", log_dir=log_dir)
    return logger, log_dir


def find_module(workcell, module_name):
    for module in workcell.modules:
        if module.name == module_name:
            return module


def check_step(exp_id, run_id, step, locations, wc_state):
    if "target" in locations:
        location = wc_state["locations"][locations["target"]]
        if not (location["state"] == "Empty") or not (
            (len(location["queue"]) > 0 and location["queue"][0] == str(run_id))
        ):
            return False

    if "source" in locations:
        location = wc_state["locations"][locations["source"]]
        if not (location["state"] == str(exp_id)):
            return False
    module_data = wc_state["modules"][step["module"]]
    if not ("BUSY" in module_data["state"]) and not (
        (len(module_data["queue"]) > 0 and module_data["queue"][0] == str(run_id))
    ):
        return False
    return True


def run_step(exp_path, wf_name, wf_id, step, locations, module, pipe, executor):
    logger, log_dir = init_logger(exp_path, wf_name, wf_id)
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


def parse_args():
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
    return parser.parse_args()


minimal_state = {
    "locations": {},
    "modules": {},
    "active_workflows": {},
    "queued_workflows": {},
    "completed_workflows": {},
    "incoming_workflows": {},
}


class Scheduler:
    def __init__(self):
        self.events = {}
        self.executor = StepExecutor()
        self.workcell = {}
        self.processes = {}
        self.redis_server = {}
        self.kafka_server = ""
        self.log_server = ""

    def run(self, args):  # noqa
        self.events = {}
        self.executor = StepExecutor()
        self.workcell = WorkcellData.from_yaml(args.workcell)
        self.processes = {}
        self.redis_server = redis.Redis(
            host=args.redis_host, port=6379, decode_responses=True
        )
        self.kafka_server = args.kafka_server
        self.log_server = args.server
        wc_state = minimal_state
        for module in self.workcell.modules:
            if module.workcell_coordinates:
                wc_coords = module.workcell_coordinates
            else:
                wc_coords = None
            wc_state["modules"][module.name] = {
                "type": module.model,
                "id": str(module.id),
                "state": "INIT",
                "queue": [],
                "location": wc_coords,
            }
        for module in self.workcell.locations:
            for location in self.workcell.locations[module]:
                if location not in wc_state["locations"]:
                    wc_state["locations"][location] = {"state": "Empty", "queue": []}
        self.redis_server.hset(name="state", mapping={"wc_state": json.dumps(wc_state)})
        print("Starting Process")
        while True:
            wc_state = json.loads(self.redis_server.hget("state", "wc_state"))
            for module in self.workcell.modules:
                # TODO: if not get_state: raise unknown
                if module.interface in Executor_Map.function:
                    first = False
                    if wc_state["modules"][module.name]["state"] == "INIT":
                        first = True
                    try:
                        interface = Executor_Map.function[module.interface]
                        state = interface.get_state(module.config)

                        if not (state == ""):
                            wc_state["modules"][module.name]["state"] = state
                        if first:
                            print("Module Found: " + str(module.name))
                    except:  # noqa
                        wc_state["modules"][module.name]["state"] = "UNKNOWN"
                        if first:
                            print("Can't Find Module: " + str(module.name))
                else:
                    # print("module interface not found")
                    pass
            for wf_id in wc_state["incoming_workflows"]:
                wf_data = wc_state["incoming_workflows"][wf_id]
                workflow_runner = WorkflowRunner(
                    yaml.safe_load(wf_data["workflow_content"]),
                    workcell=self.workcell,
                    payload=wf_data["parsed_payload"],
                    experiment_path=wf_data["experiment_path"],
                    run_id=wf_id,
                    simulate=wf_data["simulate"],
                    workflow_name=wf_data["name"],
                )
                flowdef = []
                for step in workflow_runner.steps:
                    flowdef.append(
                        {
                            "step": json.loads(step["step"].json()),
                            "locations": step["locations"],
                        }
                    )
                exp_data = Path(wf_data["experiment_path"]).name.split("_id_")
                exp_id = exp_data[-1]
                exp_name = exp_data[0]

                # To ASK RAF: should I specify this some other way?
                self.events[wf_id] = Events(
                    self.log_server,
                    "8000",
                    exp_name,
                    exp_id,
                    self.kafka_server,
                    wf_data["experiment_path"],
                )
                self.events[wf_id].log_wf_start(wf_data["name"], wf_id)

                to_queue_wf = {
                    "name": wf_data["name"],
                    "step_index": 0,
                    "flowdef": flowdef,
                    "experiment_id": exp_id,
                    "experiment_path": wf_data["experiment_path"],
                    "hist": {},
                }
                wc_state["queued_workflows"][wf_id] = to_queue_wf
                if "target" in flowdef[0]["locations"]:
                    wc_state["locations"][flowdef[0]["locations"]["target"]][
                        "queue"
                    ].append(wf_id)
                wc_state["modules"][flowdef[0]["step"]["module"]]["queue"].append(wf_id)
            for wf_id in wc_state["queued_workflows"]:
                if wf_id in wc_state["incoming_workflows"]:
                    del wc_state["incoming_workflows"][wf_id]
                wf = wc_state["queued_workflows"][wf_id]
                step_index = wf["step_index"]
                step = wf["flowdef"][step_index]["step"]
                locations = wf["flowdef"][step_index]["locations"]
                exp_id = Path(wf["experiment_path"]).name.split("_id_")[-1]
                if check_step(exp_id, wf_id, step, locations, wc_state) and not (
                    wf_id in wc_state["active_workflows"]
                ):
                    send_conn, rec_conn = mpr.Pipe()
                    module = find_module(self.workcell, step["module"])
                    step_process = mpr.Process(
                        target=run_step,
                        args=(
                            wf["experiment_path"],
                            wf["name"],
                            wf_id,
                            Step(**step),
                            locations,
                            module,
                            send_conn,
                            self.executor,
                        ),
                    )
                    step_process.start()
                    self.processes[wf_id] = {"process": step_process, "pipe": rec_conn}
                    wc_state["active_workflows"][wf_id] = wf
            cleanup_wfs = []
            for wf_id in wc_state["active_workflows"]:
                if self.processes[wf_id]["pipe"].poll():
                    response = self.processes[wf_id]["pipe"].recv()
                    locations = response["locations"]
                    step = response["step"]
                    if "target" in locations:
                        wc_state["locations"][locations["target"]]["state"] = wf[
                            "experiment_id"
                        ]
                        wc_state["locations"][locations["target"]]["queue"].remove(
                            wf_id
                        )
                    if "source" in locations:
                        wc_state["locations"][locations["source"]]["state"] = "Empty"
                    wc_state["modules"][step.module]["queue"].remove(wf_id)
                    wc_state["queued_workflows"][wf_id]["hist"][step.name] = response[
                        "step_response"
                    ]
                    step_index = wc_state["queued_workflows"][wf_id]["step_index"]
                    if step_index + 1 == len(
                        wc_state["queued_workflows"][wf_id]["flowdef"]
                    ):
                        self.events[wf_id].log_wf_end(
                            wc_state["queued_workflows"][wf_id]["name"], wf_id
                        )
                        del self.events[wf_id]
                        wc_state["completed_workflows"][wf_id] = wc_state[
                            "queued_workflows"
                        ][wf_id]
                        wc_state["queued_workflows"][wf_id]["hist"]["run_dir"] = str(
                            response["log_dir"]
                        )
                        del wc_state["queued_workflows"][wf_id]
                    else:
                        wc_state["queued_workflows"][wf_id]["step_index"] += 1
                        step_index = wc_state["queued_workflows"][wf_id]["step_index"]
                        flowdef = wc_state["queued_workflows"][wf_id]["flowdef"]
                        if "target" in flowdef[step_index]["locations"]:
                            wc_state["locations"][
                                flowdef[step_index]["locations"]["target"]
                            ]["queue"].append(wf_id)
                        wc_state["modules"][flowdef[step_index]["step"]["module"]][
                            "queue"
                        ].append(wf_id)
                    cleanup_wfs.append(wf_id)
            for wf_id in cleanup_wfs:
                del wc_state["active_workflows"][wf_id]

            self.redis_server.hset(
                name="state", mapping={"wc_state": json.dumps(wc_state)}
            )
            time.sleep(0.3)


if __name__ == "__main__":
    args = parse_args()
    scheduler = Scheduler()
    scheduler.run(args)
