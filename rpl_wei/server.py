"""The server that takes incoming WEI flow requests from the experiment application"""
import json
from argparse import ArgumentParser
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict  # , List
import os
import re
import yaml
import redis

import rq
import requests
import multiprocessing as mpr
import time
import ulid
from fastapi import FastAPI, File, Form, UploadFile, Request    
from fastapi.responses import JSONResponse
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from rq.job import Job
from rq.registry import FailedJobRegistry, FinishedJobRegistry, StartedJobRegistry
from fastapi.templating import Jinja2Templates


from rpl_wei.core.data_classes import Workcell as WorkcellData
from rpl_wei.core.workcell import Workcell
from rpl_wei.core.experiment import start_experiment
from rpl_wei.core.loggers import WEI_Logger
from rpl_wei.core.interfaces.rest_interface import RestInterface
from rpl_wei.core.interfaces.ros2_interface import ROS2Interface
from rpl_wei.core.workflow import WorkflowRunner, WorkflowData
from rpl_wei.processing.worker import run_workflow_task, task_queue

import threading

# TODO: db backup of tasks and results (can be a proper db or just a file)
# TODO logging for server and workcell
# TODO consider sub-applications for different parts of the server (e.g. /job, /queue, /data, etc.)
# TODO make the workcell live in the DATA_DIR and be coupled to the server
#      This might entail making a rq object of the wei object and making that available to the workers

workcell = None
kafka_server = None
redis_server = None
# wc_state = {"locations": {}, "modules": {}, "workflows": []}
# wf_queue = []
# templates = Jinja2Templates(directory="templates")
# running_wfs = {}
# completed_wfs = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initial run function for the app, parses the worcell argument
    Parameters
    ----------
    app : FastApi
       The REST API app being initialized
, timeout_sec=10
    Returns
    -------
    None"""
    global workcell, kafka_server, redis_server
    parser = ArgumentParser()
    parser.add_argument("--redis_host", type=str, help="url (no port) for Redis server", default="localhost")
    parser.add_argument("--workcell", type=Path, help="Path to workcell file")
    parser.add_argument(
        "--kafka-server", type=str, help="Kafka server for logging", default=None
    )
    
    redis_server = redis.Redis(host=args.redis_host, port=6379, decode_responses=True)
    args = parser.parse_args()
    with open(args.workcell) as f:
        workcell = Workcell(workcell_def=yaml.safe_load(f))
    
    # for module in workcell.locations:
    #         for location in workcell.locations[module]:
    #             if not location in wc_state["locations"]:
    #                 wc_state["locations"][location] = {"state": "Empty", "queue": []}
    # thread = threading.Thread(target=update_state)
    # thread.start()
    kafka_server = args.kafka_server

    # Yield control to the application
    yield

    # Do any cleanup here
    pass


app = FastAPI(
    lifespan=lifespan,
)
script_dir = os.path.dirname(__file__)
st_abs_file_path = os.path.join(script_dir, "static/")
app.mount("/static", StaticFiles(directory=st_abs_file_path), name="static")
templates = Jinja2Templates(directory=script_dir+"/templates")



def start_exp(experiment_id: str, experiment_name: str):
    """Pulls an experiment and creates the files and logger for it

    Parameters
    ----------
    experiment_id : str
       The programatically generated id of the experiment for the workflow

    experiment_name: str
        The human created name of the experiment

    Returns
    -------
     response: Dict
       a dictionary including the succesfulness of the queueing, the jobs ahead and the id
    """
    global kafka_server
    base_response_content = {
        "experiment_id": experiment_id,
        "experiment_name": experiment_name,
    }
    try:
        exp_data = start_experiment(experiment_name, experiment_id, kafka_server)
        # jobs_ahead = len(task_queue.jobs)
        # response_content = {
        #     "status": "success",
        #     "exp_id": experiment_id,
        #     "experiment_path"
        #     "jobs_ahead": jobs_ahead,
        #     "job_id": job.get_id(),
        #     **base_response_content,
        # }
        return JSONResponse(content=exp_data)

    except Exception as e:
        response_content = {
            "status": "failed",
            "error": str(e),
            **base_response_content,
        }
        return JSONResponse(content=response_content)



@app.post("/exp/{experiment_id}/log")
def log_experiment(experiment_path: str, log_value: str):
    """Placeholder"""
    log_dir = Path(experiment_path)
    experiment_id = log_dir.name.split("_id_")[-1]
    logger = WEI_Logger.get_logger("log_" + experiment_id, log_dir)
    logger.info(log_value)


@app.get("/exp/{experiment_id}/log")
async def log_return(experiment_path: str):
    log_dir = Path(experiment_path)
    experiment_id = log_dir.name.split("_")[-1]
    with open(log_dir / Path("log_" + experiment_id + ".log"), "r") as f:
        return f.read()



@app.post("/job/run")
async def process_job(
    workflow: UploadFile = File(...),
    payload: UploadFile = File(...),
    experiment_path: str = "",
    simulate: bool = False,
):
    """parses the payload and workflow files, and then pushes a workflow job onto the redis queue
    Parameters
    ----------
    workflow: UploadFile
        The workflow yaml file
    payload: UploadFile
        The data input file to the workflow
    experiment_path: str
       The path to the data of the experiment for the workflow
    simulate: bool
        whether to use real robots or not

    Returns
    -------
    response: Dict
       a dictionary including the succesfulness of the queueing, the jobs ahead and the id
    """
    global redis_server
    workflow_path = Path(workflow.filename)
    workflow_name = workflow_path.name.split(".")[0]

    workflow_content = await workflow.read()
    payload = await payload.read()
    # Decode the bytes object to a string
    workflow_content_str = workflow_content.decode("utf-8")
    parsed_payload = json.loads(payload)
    wc_state = json.loads(redis_server.hget("state", "wc_state"))
    job_id = ulid.new().str
    wc_state["incoming_workflows"][str(job_id)] = {"workflow_content": workflow_content_str, "parsed_payload": parsed_payload, "experiment_path": str(experiment_path), "name": workflow_name, "simulate": simulate}
    redis_server.hset(name="state", mapping={"wc_state": json.dumps(wc_state)})
    return JSONResponse(content={"status": "SUCCESS", "job_id": job_id})


@app.post("/log/{experiment_id}")
def log_experiment(experiment_path: str, log_value: str):
    """Logs a value to the experiment log fo the given path
    Parameters
    ----------
    experiment_path: str
       The path to the data of the experiment for the workflow
    log_value: str
        the value to write to the experiment log

    Returns
    -------
        None
    """
    log_dir = Path(experiment_path)
    experiment_id = log_dir.name.split("_id_")[-1]
    logger = WEI_Logger.get_logger("log_" + experiment_id, log_dir)
    logger.info(log_value)


@app.get("/log/return")
async def log_return(experiment_path: str):
    """Returns a string containing the log files for a given experiment
    Parameters
    ----------
    experiment_path: str
       The path to the data of the experiment for the workflow

    Returns
    -------
    None
    """


    log_dir = Path(experiment_path)
    experiment_id = log_dir.name.spit("_")[-1]
    with open(log_dir / Path("log_" + experiment_id + ".log"), "r") as f:
        return f.read()


@app.post("/experiment")
def process_exp(experiment_name: str, experiment_id: str):
    """Pulls an experiment and creates the files and logger for it

    Parameters
    ----------
    experiment_name: str
        The human created name of the experiment
    experiment_id : str
       The programatically generated id of the experiment for the workflow
    Returns
    -------
     response: Dict
       a dictionary including the succesfulness of the queueing, the jobs ahead and the id

    """
    
    # Decode the bytes object to a string
    # Generate ULID for the experiment, really this should be done by the client (Experiment class)
    global kafka_server
    return start_experiment(experiment_name, experiment_id, kafka_server)




@app.get("/job/{job_id}/state")
async def get_job_status(job_id: str):
    """Pulls the status of a job on the queue

    Parameters
    ----------
    job_id : str
       The programatically generated id of the experiment for the workflow


    Returns
    -------
     response: Dict
       a dictionary including the status on the queueing, and the result of the job if it's done
    """
    global redis_server
    wc_state=json.loads(redis_server.hget("state", "wc_state"))
    if job_id in wc_state["active_workflows"]:
        return JSONResponse(content={"status": "running", "result": {}})
    elif job_id in wc_state["queued_workflows"]:
        return  JSONResponse(content={"status": "queued", "result": {}})
    elif job_id in wc_state["completed_workflows"]:
        wf = wc_state["completed_workflows"][job_id]
        return  JSONResponse(content={"status": "finished", "result": wf["hist"], "run_dir": wf["hist"]["run_dir"]})
      
        
        
    return JSONResponse(content={"status": "running", "result": "result"})

@app.get("/job/{job_id}/log")
async def log_return(job_id: str,  experiment_path: str):
    """Parameters
    ----------
   

    job_id: str
        The queue job id for the job being logged
        
    experiment_path : str
       The path to the data forthe experiment for the workflow

    Returns
    -------
    response: str
       a string with the log data for the run requested"""
    log_dir = Path(experiment_path)
    for file in os.listdir( log_dir / 
                           'wei_runs' ):
        if re.match(".*"+job_id, file):
             with open(log_dir /"wei_runs"/ file  / "runLogger.log") as f:
                           return f.read()
    


@app.get("/wc/state", response_class=HTMLResponse)
def show():
    """
     
     Describes the state of the whole workcell including locations and daemon states

    Parameters
    ----------
    None
    
     Returns
    -------
     response: Dict
       the state of the workcell
    """
     
    global redis_server
    wc_state = json.loads(redis_server.hget("state", "wc_state"))
    return JSONResponse(content={"wc_state": json.dumps(wc_state)}) #templates.TemplateResponse("item.html", {"request": request, "wc_state": wc_state})




@app.get("/wc/locations/all_states")
def show_states():
    """
     
     Describes the state of the workcell locations 
    Parameters
    ----------
    None
    
     Returns
    -------
     response: Dict
       the state of the workcell locations, with the id of the run that last filled the location
    """
    
    global redis_server
    wc_state = json.loads(redis_server.hget("state", "wc_state"))
    
    return JSONResponse(content={"location_states": wc_state["locations"] })

@app.get("/wc/locations/{location}/state")
def loc(location: str):
    """
     
    Describes the state of the workcell locations 
    Parameters
    ----------
    None
    
     Returns
    -------
     response: Dict
       the state of the workcell locations, with the id of the run that last filled the location
     """
    global redis_server
    wc_state = json.loads(redis_server.hget("state", "wc_state"))

    
    return JSONResponse(content={str(location): wc_state["locations"][location] })

@app.get("/wc/modules/{module}/state")
def mod(module: str):
    """
     
    Describes the state of the workcell locations 
    Parameters
    ----------
    None
    
     Returns
    -------
     response: Dict
       the state of the workcell locations, with the id of the run that last filled the location
     """
    global redis_server
    wc_state = json.loads(redis_server.hget("state", "wc_state"))
    return JSONResponse(content={str(module): wc_state["modules"][module] })

@app.post("/wc/locations/{location}/set")
async def update(location: str, experiment_id: str):
    global redis_server
    wc_state = json.loads(redis_server.hget("state", "wc_state"))

    if experiment_id == "":
         wc_state["locations"][location]["state"] = "Empty"
    else:
         wc_state["locations"][location]["state"] = experiment_id
    redis_server.hset("state", "wc_state", json.dumps(wc_state))
    return JSONResponse(content={"State": wc_state })


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "rpl_wei.server:app",
        reload=False,
        ws_max_size=10000000000000000000000000000000000000000000000000000000000000000000000000,
    )
