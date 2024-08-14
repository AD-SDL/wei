"""
Router for the "runs" endpoints
"""

import json
import os
import traceback
from typing import Annotated, Any, Dict, Optional

import yaml
from fastapi import APIRouter, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from wei.core.loggers import Logger
from wei.core.state_manager import state_manager
from wei.core.storage import get_workflow_run_directory, get_workflow_run_log_path
from wei.core.workflow import create_run, save_workflow_files
from wei.types import Workflow, WorkflowStatus
from wei.types.datapoint_types import DataPoint

router = APIRouter()


@router.post("/start")
async def start_run(
    request: Request,
    experiment_id: Annotated[str, Form()],
    workflow: Annotated[str, Form()],
    payload: Annotated[Optional[str], Form()] = None,
    simulate: Annotated[Optional[bool], Form()] = False,
    files: list[UploadFile] = [],  # noqa B006
) -> JSONResponse:
    """
    parses the payload and workflow files, and then pushes a workflow job onto the redis queue

    Parameters
    ----------
    workflow: UploadFile
    - The workflow yaml file
    payload: Optional[Dict[str, Any]] = {}
    - Dynamic values to insert into the workflow file
    experiment_id: str
    - The id of the experiment this workflow is associated with
    simulate: bool
    - whether to use real robots or not

    Returns
    -------
    response: Dict
    - a dictionary including whether queueing succeeded, the jobs ahead, and the id
    """
    try:
        wf = Workflow.model_validate_json(workflow)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e)) from e

    if payload is None:
        payload = {}
    else:
        payload = json.loads(payload)
        if not isinstance(payload, dict) or not all(
            isinstance(k, str) for k in payload.keys()
        ):
            raise HTTPException(
                status_code=400, detail="Payload must be a dictionary with string keys"
            )
    logger = Logger.get_experiment_logger(experiment_id)
    logger.debug(f"Received job run request: {wf.name}")
    workcell = state_manager.get_workcell()

    wf_run = create_run(wf, workcell, experiment_id, payload, simulate)
    wf_run = save_workflow_files(wf_run, files)

    with state_manager.wc_state_lock():
        state_manager.set_workflow_run(wf_run)
    return JSONResponse(
        content={
            "wf": wf_run.model_dump(mode="json"),
            "run_id": wf_run.run_id,
            "status": str(wf_run.status),
        }
    )


@router.post("/validate")
async def validate_workflow(
    experiment_id: str,
    workflow: UploadFile,
    payload: Dict[str, Any] = None,
) -> JSONResponse:
    """Validate a workflow file against the current workcell"""
    if payload is None:
        payload = {}
    wf = None
    wf_run = None
    try:
        workflow_content = await workflow.read()
        workflow_content_str = workflow_content.decode("utf-8")
        wf = Workflow(**yaml.safe_load(workflow_content_str))
        logger = Logger.get_experiment_logger(experiment_id)
        logger.debug(f"Received job run request: {wf.name}")
        workcell = state_manager.get_workcell()

        wf_run = create_run(wf, workcell, experiment_id, payload)

        return JSONResponse(
            content={
                "valid": True,
                "wf": wf_run.model_dump(mode="json"),
                "error": None,
            }
        )
    except Exception as e:
        if wf_run:
            return JSONResponse(
                status_code=400,
                content={
                    "valid": False,
                    "wf": wf_run.model_dump(mode="json"),
                    "error": f"Error: {e}",
                },
            )
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "valid": False,
                    "wf": wf_run.model_dump(mode="json"),
                    "error": f"Error: {e}",
                },
            )


@router.get("/{run_id}/state")
def get_run_status(
    run_id: str,
) -> JSONResponse:
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
    try:
        with state_manager.wc_state_lock():
            workflow = state_manager.get_workflow_run(run_id)
        return JSONResponse(content=workflow.model_dump(mode="json"))
    except KeyError:
        return JSONResponse(content={"status": WorkflowStatus.UNKNOWN})


@router.get("/{run_id}/log")
async def log_run_return(run_id: str) -> str:
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

    with open(get_workflow_run_log_path(run_id)) as f:
        return f.read()


@router.get("/{run_id}/results")
@router.get("/{run_id}/files")
async def get_wf_files(run_id: str) -> Dict:
    """Returns the list of files in a given workflow run's result directory."""
    return {"files": os.listdir(get_workflow_run_directory(run_id))}


@router.get("/{run_id}/file")
async def get_wf_file(run_id: str, filename: str) -> FileResponse:
    """Returns a specific file from a workflow run's result directory."""
    return FileResponse(get_workflow_run_directory(run_id) / filename)


@router.get("/data/{datapoint_id}")
async def get_datapoint(datapoint_id: str):
    """Returns a specific datapoint from a workflow run's result directory."""
    datapoint = state_manager.get_datapoint(datapoint_id)
    if datapoint.type == "local_file":
        return FileResponse(datapoint.path)
    else:
        return JSONResponse({"value": datapoint.value})


@router.get("/data/{datapoint_id}/info")
async def get_datapoint_info(datapoint_id: str) -> DataPoint:
    """Returns a specific datapoint from a workflow run's result directory."""
    datapoint = state_manager.get_datapoint(datapoint_id)
    return datapoint
