"""The server that takes incoming WEI flow requests from the experiment application"""
"""The server that takes incoming WEI flow requests from the experiment application"""
import json
from argparse import ArgumentParser
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List

import rq
import ulid
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import JSONResponse
from rq.job import Job
from rq.registry import FailedJobRegistry, FinishedJobRegistry, StartedJobRegistry

from rpl_wei.core import DATA_DIR
from rpl_wei.core.data_classes import Workcell
from rpl_wei.core.experiment import start_experiment
from rpl_wei.core.loggers import WEI_Logger
from rpl_wei.processing.worker import run_workflow_task, task_queue

# TODO: db backup of tasks and results (can be a proper db or just a file)
# TODO logging for server and workcell
# TODO consider sub-applications for different parts of the server (e.g. /job, /queue, /data, etc.)
# TODO make the workcell live in the DATA_DIR and be coupled to the server
#      This might entail making a rq object of the wei object and making that available to the workers

workcell = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initial run function for the app, parses the worcell argument
        Parameters
        ----------
        app : FastApi
           The REST API app being initialized

        Returns
        -------
        None"""
    global workcell
    parser = ArgumentParser()
    parser.add_argument("--workcell", type=Path, help="Path to workcell file")

    args = parser.parse_args()
    workcell = Workcell.from_yaml(args.workcell)

    # Yield control to the application
    yield

    # Do any cleanup here
    pass


app = FastAPI(lifespan=lifespan, )


def submit_job(
    experiment_path: str,
    workflow_content_str: str,
    parsed_payload: Dict[str, Any],
    simulate: bool,
    workflow_name: str
):
    
    """puts a workflow job onto the redis queue

        Parameters
        ----------
        experiment_id : str
           The id of the experiment for the workflow

        workflow_content_str: str
            The defintion of the workflow from the workflow yaml file

        parsed_payload: Dict
            The data input to the workflow
        
        
        simulate: bool
            whether to use real robots or not
        

        Returns
        -------
        response: Dict
           a dictionary including the succesfulness of the queueing, the jobs ahead and the id"""
    # manually create job ulid (so we can use it for the loggign inside wei)
    job_id = ulid.new().str
    path = Path(experiment_path)
    experiment_id = path.name.split("_")[-1]
    base_response_content = {
        "experiment_id": experiment_path,
    }
    try:
        job = task_queue.enqueue(
            run_workflow_task,
            experiment_path,
            experiment_id,
            workflow_content_str,
            parsed_payload,
            workcell.__dict__,
            job_id,
            simulate,
            workflow_name,
            job_id=job_id,
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
    base_response_content = {
        "experiment_id": experiment_id,
        "experiment_name": experiment_name,
    }
    
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
           a dictionary including the succesfulness of the queueing, the jobs ahead and the id"""
    
    try:
       
        exp_data = start_experiment(experiment_name, experiment_id)
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


@app.post("/job")
async def process_job(
    workflow: UploadFile = File(...),
    payload: UploadFile = File(...),
    experiment_path: str = "",
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
           a dictionary including the succesfulness of the queueing, the jobs ahead and the id"""
    workflow_path = Path(workflow.filename)
    workflow_name = workflow_path.name.split(".")[0]
  
    workflow_content = await workflow.read()
    payload = await payload.read()
    # Decode the bytes object to a string
    workflow_content_str = workflow_content.decode("utf-8")
    parsed_payload = json.loads(payload)
    
    return submit_job(
        experiment_path, workflow_content_str, parsed_payload, workflow_name=workflow_name, simulate=simulate, 
    )


@app.post("/log/{experiment_id}")
async def log_experiment(experiment_path: str, log_value: str):
    """Placeholder"""
    log_dir = Path(experiment_path)
    experiment_id = log_dir.name.spit("_")[-1]
    logger = WEI_Logger.get_logger("log_" + experiment_id, log_dir)
    logger.info(log_value)


@app.get("/log/return")
async def log_experiment(experiment_path: str):
    log_dir = Path(experiment_path)
    experiment_id = log_dir.name.spit("_")[-1]
    with open(log_dir / Path("log_" + experiment_id + ".log"), "r") as f:
        return(f.read())

   
@app.post("/experiment")
async def process_exp(experiment_name: str, experiment_id: str):
    """ Pulls an experiment and creates the files and logger for it

        Parameters
        ----------
        experiment_id : str
           The progromatically generated id of the experiment for the workflow

        experiment_name: str
            The human created name of the experiment

        

        Returns
        -------
         response: Dict
           a dictionary including the succesfulness of the queueing, the jobs ahead and the id"""
    
    # Decode the bytes object to a string
    # Generate ULID for the experiment, really this should be done by the client (Experiment class)
    return start_exp(experiment_id, experiment_name)


@app.post("/job/{experiment_id}")
async def process_job_with_id(
    experiment_id: str,
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
           a dictionary including the succesfulness of the queueing, the jobs ahead and the id"""
    workflow_content = await workflow.read()
    workflow_content_str = workflow_content.decode("utf-8")

    parsed_payload = json.loads(payload)

    return submit_job(
        experiment_id, workflow_content_str, parsed_payload, simulate=simulate
    )


@app.get("/job/{job_id}")
async def get_job_status(job_id: str):
    """ Pulls the status of a job on the queue
        
        Parameters
        ----------
        job_id : str
           The progromatically generated id of the experiment for the workflow


        Returns
        -------
         response: Dict
           a dictionary including the status on the queueing, and the result of the job if it's done"""
    
    try:
        job = Job.fetch(job_id, connection=task_queue.connection)
    except rq.exceptions.NoSuchJobError:
        return JSONResponse(content={"status": "failed", "error": "No such job"})

    job_status = job.get_status()
    result = job.result

    return JSONResponse(content={"status": job_status, "result": result})


@app.get("/queue/info")
async def queue_info():
    """ Pulls the status of the queue
        
        Parameters
        ----------
        None


        Returns
        -------
         response: Dict
           the number of jobs on the queue, the number that have been started, the number that have been completed on this run, and the number that have failed."""
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


if __name__ == "__main__":
    import uvicorn
    print("asdfsaf")
    uvicorn.run("rpl_wei.server:app", reload=True, ws_max_size=10000000000000000000000000000000000000000000000000000000000000000000000000,)
