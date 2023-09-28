"""The server that takes incoming WEI flow requests from the experiment application"""
import json
import os
import re
from argparse import ArgumentParser
from contextlib import asynccontextmanager
from pathlib import Path

import ulid
import yaml
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse

from wei.core.data_classes import ExperimentStatus, WorkflowStatus
from wei.core.experiment import start_experiment
from wei.core.loggers import WEI_Logger
from wei.core.workcell import Workcell
from wei.state_manager import StateManager

# TODO: db backup of tasks and results (can be a proper db or just a file)
# TODO logging for server and workcell
# TODO make the workcell live in the DATA_DIR and be coupled to the server
#      This might entail making a rq object of the wei object and making that available to the workers

workcell = None
kafka_server = None
state_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initial run function for the app, parses the workcell argument
        Parameters
        ----------
        app : FastApi
           The REST API app being initialized
    , timeout_sec=10
        Returns
        -------
        None"""
    global workcell, kafka_server, state_manager
    parser = ArgumentParser()
    parser.add_argument(
        "--redis_host",
        type=str,
        help="url (no port) for Redis server",
        default="localhost",
    )
    parser.add_argument("--workcell", type=Path, help="Path to workcell file")
    parser.add_argument(
        "--kafka-server", type=str, help="Kafka server for logging", default=None
    )

    args = parser.parse_args()
    with open(args.workcell) as f:
        workcell = Workcell(workcell_def=yaml.safe_load(f))
    state_manager = StateManager(
        workcell.workcell.name, redis_host=args.redis_host, redis_port=6379
    )

    kafka_server = args.kafka_server

    # Yield control to the application
    yield

    # Do any cleanup here
    pass


app = FastAPI(
    lifespan=lifespan,
)


def start_exp(experiment_id: str, experiment_name: str) -> JSONResponse:
    """Pulls an experiment and creates the files and logger for it

    Parameters
    ----------
    experiment_id : str
       The programmatically generated id of the experiment for the workflow

    experiment_name: str
        The human created name of the experiment

    Returns
    -------
     response: Dict
       a dictionary including the successfulness of the queueing, the jobs ahead and the id
    """
    global kafka_server
    base_response_content = {
        "experiment_id": experiment_id,
        "experiment_name": experiment_name,
        "status": ExperimentStatus.CREATED,
    }
    try:
        exp_data = start_experiment(experiment_name, experiment_id, kafka_server)
        return JSONResponse(content=exp_data)

    except Exception as e:
        response_content = {
            "status": ExperimentStatus.FAILED,
            "error": str(e),
            **base_response_content,
        }
        return JSONResponse(content=response_content)


@app.post("/exp/{experiment_id}/log")
def log_experiment(experiment_path: str, log_value: str) -> None:
    """Logs a value to the log file for a given experiment"""
    log_dir = Path(experiment_path)
    experiment_id = log_dir.name.split("_id_")[-1]
    logger = WEI_Logger.get_logger("log_" + experiment_id, log_dir)
    logger.info(log_value)


@app.get("/exp/{experiment_id}/log")
async def log_return(experiment_path: str) -> str:
    """Returns the log for a given experiment"""
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
) -> JSONResponse:
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
       a dictionary including whether queueing succeeded, the jobs ahead, and the id
    """
    log_dir = Path(experiment_path)
    experiment_id = log_dir.name.split("_")[-1]
    logger = WEI_Logger.get_logger("log_" + experiment_id, log_dir)
    logger.info("Received job run request")
    global state_manager
    workflow_path = Path(workflow.filename)
    workflow_name = workflow_path.name.split(".")[0]

    workflow_content = await workflow.read()
    payload = await payload.read()
    # Decode the bytes object to a string
    workflow_content_str = workflow_content.decode("utf-8")
    parsed_payload = json.loads(payload)
    job_id = ulid.new().str
    state_manager.incoming_workflows.put(
        {
            "wf_id": job_id,
            "workflow_content": workflow_content_str,
            "parsed_payload": parsed_payload,
            "experiment_path": str(experiment_path),
            "name": workflow_name,
            "simulate": simulate,
        }
    )
    logger.info("Queued: " + str(job_id))
    return JSONResponse(content={"status": WorkflowStatus.QUEUED, "job_id": job_id})


@app.post("/experiment")
def process_exp(experiment_name: str, experiment_id: str) -> dict:
    """Pulls an experiment and creates the files and logger for it

    Parameters
    ----------
    experiment_name: str
        The human created name of the experiment
    experiment_id : str
       The programmatically generated id of the experiment for the workflow
    Returns
    -------
     response: Dict
       a dictionary including the successfulness of the queueing, the jobs ahead and the id

    """

    # Decode the bytes object to a string
    # Generate ULID for the experiment, really this should be done by the client (Experiment class)
    global kafka_server
    return start_experiment(experiment_name, experiment_id, kafka_server)


@app.get("/job/{job_id}/state")
async def get_job_status(job_id: str) -> JSONResponse:
    """Pulls the status of a job on the queue

    Parameters
    ----------
    job_id : str
       The programmatically generated id of the experiment for the workflow


    Returns
    -------
     response: Dict
       a dictionary including the status on the queueing, and the result of the job if it's done
    """
    global state_manager
    try:
        workflow = state_manager.workflows[job_id]
        return JSONResponse(
            content={
                "status": workflow["status"],
                "result": workflow["result"],
            }
        )
    except KeyError:
        return JSONResponse(content={"status": WorkflowStatus.UNKNOWN})


@app.get("/job/{job_id}/log")
async def log_job_return(job_id: str, experiment_path: str) -> str:
    """Parameters
    ----------


    job_id: str
        The queue job id for the job being logged

    experiment_path : str
       The path to the data for the experiment for the workflow

    Returns
    -------
    response: str
       a string with the log data for the run requested"""
    log_dir = Path(experiment_path)
    for file in os.listdir(log_dir / "wei_runs"):
        if re.match(".*" + job_id, file):
            with open(log_dir / "wei_runs" / file / "runLogger.log") as f:
                return f.read()


@app.get("/wc/state", response_class=HTMLResponse)
def show() -> JSONResponse:
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
    global state_manager

    wc_state = json.loads(state_manager.get_state())
    return JSONResponse(
        content={"wc_state": json.dumps(wc_state)}
    )  # templates.TemplateResponse("item.html", {"request": request, "wc_state": wc_state})


@app.get("/wc/locations/all_states")
def show_states() -> JSONResponse:
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

    global state_manager

    return JSONResponse(
        content={"location_states": str(state_manager.locations.to_dict())}
    )


@app.get("/wc/locations/{location}/state")
def loc(location: str) -> JSONResponse:
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
    global state_manager

    try:
        return JSONResponse(
            content={str(location): str(state_manager.locations[location])}
        )
    except KeyError:
        return HTTPException(status_code=404, detail="Location not found")


@app.get("/wc/modules/{module_name}/state")
def mod(module_name: str) -> JSONResponse:
    """
    Gets the state of a given module
    Parameters
    ----------
    module_name: the name of the module to get the state of

     Returns
    -------
     response: Dict
       the state of the requested module
    """
    global state_manager

    try:
        return JSONResponse(
            content={str(module_name): str(state_manager.modules[module_name])}
        )
    except KeyError:
        return HTTPException(status_code=404, detail="Module not found")


@app.post("/wc/locations/{location_name}/set")
async def update(location_name: str, experiment_id: str) -> JSONResponse:
    """
    Manually update the state of a location in the workcell.
    Parameters
    ----------
    location: the name of the location to update
    experiment_id: the id of the experiment that is in the location

    Returns
    -------
        response: Dict
         the state of the workcell locations, with the id of the run that last filled the location
    """
    global state_manager

    def update_location_state(location: dict, value: str) -> dict:
        location["state"] = "Empty"
        return location

    with state_manager.state_lock():
        if experiment_id == "":
            state_manager.update_location(location_name, update_location_state, "Empty")
        else:
            state_manager.update_location(
                location_name, update_location_state, experiment_id
            )
        return JSONResponse(
            content={"Locations": str(state_manager.locations.to_dict())}
        )


@app.delete("/wc/workflows/clear")
async def clear_workflows() -> JSONResponse:
    """
    Clears the completed and failed workflows from the workcell
    Parameters
    ----------
    None

    Returns
    -------
        response: Dict
         the state of the workflows
    """
    global state_manager
    with state_manager.state_lock():
        for wf_id, workflow in state_manager.workflows:
            if (
                workflow["status"] == WorkflowStatus.COMPLETED
                or workflow["status"] == WorkflowStatus.FAILED
            ):
                del state_manager.workflows[wf_id]
        return JSONResponse(
            content={"Workflows": str(state_manager.workflows.to_dict())}
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "wei.server:app",
        reload=False,
        ws_max_size=10000000000000000000000000000000000000000000000000000000000000000000000000,
    )
