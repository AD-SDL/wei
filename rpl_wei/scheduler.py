import threading
import redis
from rpl_wei.core.data_classes import Workcell as WorkcellData
from rpl_wei.core.workcell import Workcell
from rpl_wei.core.loggers import WEI_Logger
from rpl_wei.core.interfaces.rest_interface import RestInterface
from rpl_wei.core.step_executor import StepExecutor
from rpl_wei.core.interfaces.ros2_interface import ROS2Interface
from rpl_wei.core.workflow import WorkflowRunner, WorkflowData
import yaml
from pathlib import Path
from argparse import ArgumentParser
import time
import json
import multiprocessing as mpr
def check_step(exp_id, run_id, step, locations, wc_state):
    if "target" in locations: 
                location = wc_state["locations"][locations["target"]]
                if not(wc_state["state"] == "Empty") or not((len(location["queue"]) > 0 and location["queue"][0] == str(run_id))):
                        return False
            
    if "source" in locations:          
                location = wc_state["locations"][locations["source"]]
                if not(location["state"] == str(exp_id)):
                        return False
    module_data = wc_state["modules"][step["module"]]
    if not("BUSY" in module_data["state"]) and not((len(module_data["queue"]) > 0 and module_data["queue"][0] == str(run_id))):
                        return False
    return True
def run_step(step, locations, module, pipe, executor):
      action_response, action_msg, action_log =  executor.execute_step(step, module)
      pipe.send({"step_response": {"action_response": action_response, "action_message": action_msg, "action_log": action_log}, "step": step, "locations": locations})
      
if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--workcell", type=Path, help="Path to workcell file")
    redis_server = redis.Redis(host='localhost', port=6379, decode_responses=True)
    args = parser.parse_args()
    INTERFACES = {"wei_rest_node": RestInterface}  #"wei_ros_node": ROS2Interface("stateNode")}
    executor = StepExecutor()
    workcell = WorkcellData.from_yaml(args.workcell)
    processes = {}
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    wc_state = {"locations": {}, "modules": {}, "active_workflows": {}, "queued_workflows": {}, "completed_workflows": {}, "incoming_workflows": {}}
    for module in workcell.modules:
        wc_state["modules"][module["name"]] = {"type": module["type"], "id": str(module["id"]), "state": "Empty", "queue": []}
    for module in workcell.locations:
        for location in workcell.locations[module]:
            if not location in wc_state["locations"]:
                    wc_state["locations"][location] = {"state": "Empty", "queue": []}
    r.hset(name="state", mapping={"wc_state": json.dumps(wc_state)})

    while True:
        wc_state = json.loads(r.hget("state", "wc_state"))
        for module in workcell.workcell.modules:
                #TODO: if not get_state: raise unknown
                if module.interface in INTERFACES:

                    try:
                        interface = INTERFACES[module.interface]
                        state = interface.get_state(module.config)
                    
                        if not(state == ""):
                            wc_state["modules"][module.name]["state"] = state
                    except:
                            wc_state["modules"][module.name] = "UNKNOWN"
                else:
                    # print("module interface not found")
                    pass
        for wf_id in wc_state["incoming_workflows"]:
            wf_data = wc_state["incoming_workflows"][wf_id]
            workflow_runner = WorkflowRunner(
                yaml.safe_load(wf_data["workflow_content_str"]),
                workcell=workcell,
                payload=wf_data["parsed_payload"],
                experiment_path=wf_data["experiment_path"],
                run_id=wf_id,  
                simulate=wf_data["simulate"],
                workflow_name=wf_data["workflow_name"],
            )
            flowdef=[]
            for step in workflow_runner.steps:
                flowdef.append({"step": step["step"], "locations": step["locations"]})
            to_queue_wf = {"step_index": 0, "flowdef": flowdef, "experiment_path": wf_data["experiment_path"], "hist": {}}
            wc_state["queued_workflows"][wf_id] = to_queue_wf
            if "target" in flowdef[0]["locations"]:
                  wc_state["locations"][flowdef[0]["locations"]["target"]]["queue"].append(wf_id)
            wc_state["modules"][flowdef[0]["step"]["module"]]["queue"].append(wf_id)
        for wf_id in wc_state["queued_workflows"]:
            wf = wc_state["queued_workflows"][wf_id]
            step_index = wf["step_index"]
            step = wf["flowdef"][step_index]["step"]
            locations = wf["flowdef"][step_index]["locations"]
            if check_step(step, locations, wc_state) and not(wf_id in wc_state["active_workflows"]):
            
                send_conn, rec_conn = mpr.Pipe()
                module = workcell.workcell.modules[step["module"]]
                step_process = mpr.Process(target=run_step, args=(step, locations, module, send_conn, executor))
                step_process.start()
                processes[wf_id] = {"process": step_process, "pipe": rec_conn}
                wc_state["active_workflows"][wf_id] = wf
        for wf_id in wc_state["active_workflows"]:
            if processes[wf_id]["pipe"].poll():
                    response = processes[wf_id]["pipe"].recv()
                    locations = response["locations"]
                    step = response["step"]
                    if "target" in locations:
                        wc_state["locations"][locations["target"]]["state"] = wf["experiment_id"]
                        wc_state["locations"][locations["target"]]["queue"].remove(wf_id)
                    if "source" in locations:
                        wc_state["locations"][locations["source"]]["state"] = "Empty"
                    wc_state["mocules"][step["module"]]["queue"].remove(wf_id)
                    wc_state["queued_workflows"]["hist"][step["name"]] = response["step_response"]
                    step_index = wc_state["queued_workflows"][wf_id]["step_index"]
                    if step_index + 1 == len(wc_state["queued_workflows"]["flowdef"]):
                            wc_state["completed_workflows"][wf_id] = wc_state["queued_workflows"][wf_id]
                            del wc_state["queued_workflows"][wf_id]
                    else:
                        wc_state["queued_workflows"][wf_id]["step_index"] += 1
                        step_index = wc_state["queued_workflows"][wf_id]["step_index"]
                        flowdef = wc_state["queued_workflows"][wf_id]["flowdef"]
                        if "target" in flowdef[step_index]["locations"]:
                            wc_state["locations"][flowdef[step_index]["locations"]["target"]]["queue"].append(wf_id)
                        wc_state["modules"][flowdef[step_index]["step"]["module"]]["queue"].append(wf_id)

                    del wc_state["active_workflows"[wf_id]]
                            
                    
        r.hset(name="state", mapping={"wc_state": json.dumps(wc_state)})
        time.sleep(0.3)

     