"""The server that takes incoming WEI flow requests from the experiment application"""
import json
from argparse import ArgumentParser
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict  # , List
import os
import re

import rq
import requests
import time
import ulid
from fastapi import FastAPI, File, Form, UploadFile, Request    
from fastapi.responses import JSONResponse
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from rq.job import Job
from rq.registry import FailedJobRegistry, FinishedJobRegistry, StartedJobRegistry
from fastapi.templating import Jinja2Templates


from rpl_wei.core.data_classes import Workcell
from rpl_wei.core.experiment import start_experiment
from rpl_wei.core.loggers import WEI_Logger
from rpl_wei.core.interfaces.rest_interface import RestInterface
from rpl_wei.core.interfaces.ros2_interface import ROS2Interface
from rpl_wei.processing.worker import run_workflow_task, task_queue

import threading

# TODO: db backup of tasks and results (can be a proper db or just a file)
# TODO logging for server and workcell
# TODO consider sub-applications for different parts of the server (e.g. /job, /queue, /data, etc.)
# TODO make the workcell live in the DATA_DIR and be coupled to the server
#      This might entail making a rq object of the wei object and making that available to the workers

workcell = None
kafka_server = None
wc_state = {"locations": {}, "modules": {}}

templates = Jinja2Templates(directory="templates")

INTERFACES = {"wei_rest_node": RestInterface,  "wei_ros_node": ROS2Interface("stateNode")}
print(INTERFACES)

def update_state():
    global wc_state, workcell
    while workcell:
        
        for module in workcell.modules:
                if module.interface in INTERFACES:

                    try:
                     interface = INTERFACES[module.interface]
                     state = interface.get_state(module.config)
                   
                     if not(state == ""):
                         wc_state["modules"][module.name] = state
                    except:
                         wc_state["modules"][module.name] = "UNKNOWN"
                else:
                   # print("module interface not found")
                   pass
        
        time.sleep(0.3)

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
    global workcell, kafka_server, wc_state
    parser = ArgumentParser()
    parser.add_argument("--workcell", type=Path, help="Path to workcell file")
    parser.add_argument(
        "--kafka-server", type=str, help="Kafka server for logging", default=None
    )
    args = parser.parse_args()
    workcell = Workcell.from_yaml(args.workcell)
    for location in workcell.locations["workcell"]:
            wc_state["locations"][location] = "Empty"
    thread = threading.Thread(target=update_state)
    thread.start()
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

def submit_job(
    experiment_path: str,
    workflow_content_str: str,
    parsed_payload: Dict[str, Any],
    simulate: bool,
    workflow_name: str,
):
    """puts a workflow job onto the redis queue

    Parameters
    ----------
    experiment_path : str
       The path of the data fort experiment for the workflow

    workflow_content_str: str
        The defintion of the workflow from the workflow yaml file

    parsed_payload: Dict
        The data input to the workflow


    simulate: bool
        whether to use real robots or not


    Returns
    -------
    response: Dict
       a dictionary including the succesfulness of the queueing, the jobs ahead and the id
    """
    # manually create job ulid (so we can use it for the loggign inside wei)
    global kafka_server
    job_id = ulid.new().str
    path = Path(experiment_path)
    experiment_id = path.name.split("_id_")[-1]
    experiment_name = path.name.split("_id_")[0]
    base_response_content = {
        "experiment_path": experiment_path,
    }
    try:
        job = task_queue.enqueue(
            run_workflow_task,
            experiment_path,
            experiment_id,
            experiment_name,
            workflow_content_str,
            parsed_payload,
            workcell.__dict__,
            job_id,
            simulate,
            workflow_name,
            job_id=job_id,
            kafka_server=kafka_server,
        )
        jobs_ahead = len(task_queue.jobs)
        response_content = {
            "status": "success",
            "jobs_ahead": jobs_ahead,
            "job_id": job.get_id(),
            **base_response_content,
        }
        return JSONResponse(content=response_content)
    except Exception as e:
        response_content = {
            "status": "failed",
            "error": str(e),
            **base_response_content,
        }
        return JSONResponse(content=response_content)


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


@app.post("/exp/start")
def process_exp(experiment_name: str, experiment_id: str):
    """Pulls an experiment and creates the files and logger for it

    Parameters
    ----------
    experiment_id : str
       The progromatically generated id of the experiment for the workflow

    experiment_name: str
        The human created name of the experiment



    Returns
    -------
     response: Dict
       a dictionary including the succesfulness of the queueing, the jobs ahead and the id
    """
    global kafka_server
    # Decode the bytes object to a string
    # Generate ULID for the experiment, really this should be done by the client (Experiment class)
    return start_experiment(experiment_name, experiment_id, kafka_server)


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
    workflow_path = Path(workflow.filename)
    workflow_name = workflow_path.name.split(".")[0]

    workflow_content = await workflow.read()
    payload = await payload.read()
    # Decode the bytes object to a string
    workflow_content_str = workflow_content.decode("utf-8")
    parsed_payload = json.loads(payload)
    return submit_job(
        experiment_path,
        workflow_content_str,
        parsed_payload,
        workflow_name=workflow_name,
        simulate=simulate,
    )


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


@app.post("/job/{experiment_id}")
async def process_job_with_id(
    experiment_id: str,
    experiment_name: str,
    workflow: UploadFile = File(...),
    payload: str = Form("{}"),
    simulate: bool = False,
):
    """parses the payload and workflow files, and then pushes a workflow job onto the redis queue

    Parameters
    ----------
    experiment_id : str
       The id of the experiment for the workflow

    workflow: UploadFile
        The workflow yaml file

    payload: UploadFile
        The data input file to the workflow


    simulate: bool
        whether to use real robots or not


    Returns
    -------
    response: Dict
       a dictionary including the succesfulness of the queueing, the jobs ahead and the id
    """
    workflow_content = await workflow.read()
    workflow_content_str = workflow_content.decode("utf-8")

    parsed_payload = json.loads(payload)
    return submit_job(
        experiment_id,
        experiment_name,
        workflow_content_str,
        parsed_payload,
        simulate=simulate,
    )


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

    try:
        job = Job.fetch(job_id, connection=task_queue.connection)
    except rq.exceptions.NoSuchJobError:
        return JSONResponse(content={"status": "failed", "error": "No such job"})

    job_status = job.get_status()
    result = job.result

    return JSONResponse(content={"status": job_status, "result": result})

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
    
@app.get("/job/queue")
async def queue_info():
    """Pulls the status of the queue

    Parameters
    ----------
    None


    Returns
    -------
     response: Dict
       the number of jobs on the queue, the number that have been started, the number that have been completed on this run, and the number that have failed.
    """
    # TODO: what more information can we get from the queue?
    queued_jobs = task_queue.count
    started_registry = StartedJobRegistry(queue=task_queue)
    started_jobs = len(started_registry)
    finished_registry = FinishedJobRegistry(queue=task_queue)
    finished_jobs = len(finished_registry)
    failed_registry = FailedJobRegistry(queue=task_queue)
    failed_jobs = len(failed_registry)

    return JSONResponse(
        content={
            "queued_jobs": queued_jobs,
            "started_jobs": started_jobs,
            "finished_jobs": finished_jobs,
            "failed_jobs": failed_jobs,
        }
    )






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
     
    global wc_state
    return JSONResponse(content={"wc_state": json.dumps(wc_state)}) #templates.TemplateResponse("item.html", {"request": request, "wc_state": wc_state})

@app.get("/wc/locations/all_states")
def show_states():
    global wc_state
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
    
    
    return JSONResponse(content={"location_states": wc_state["locations"] })

@app.get("/wc/locations/{location}/state")
def update(location: str):
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
    global wc_state
    

    
    return JSONResponse(content={str(location): wc_state["locations"][location] })

@app.post("/wc/locations/{location}/set")
def update(location: str, run_id: str):
    global wc_state
    if run_id == "":
         wc_state["locations"][location] = "Empty"
    else:
         wc_state["locations"][location] = run_id

    
    return JSONResponse(content={"State": wc_state })



if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "rpl_wei.server:app",
        reload=False,
        ws_max_size=10000000000000000000000000000000000000000000000000000000000000000000000000,
    )
