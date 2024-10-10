"""
Router for the "runs" endpoints
"""

import json
import os
import traceback
from typing import Annotated, Dict, Optional

from fastapi import APIRouter, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from wei.core.loggers import Logger
from wei.core.state_manager import state_manager
from wei.core.storage import get_workflow_run_directory, get_workflow_run_log_path
from wei.core.workflow import create_run, save_workflow_files
from wei.types import Workflow
from wei.types.workflow_types import WorkflowRun

router = APIRouter()


@router.post("/start")
async def start_run(
    experiment_id: Annotated[str, Form()],
    workflow: Annotated[str, Form()],
    payload: Annotated[Optional[str], Form()] = None,
    simulate: Annotated[Optional[bool], Form()] = False,
    validate_only: Annotated[Optional[bool], Form()] = False,
    files: list[UploadFile] = [],  # noqa B006
) -> WorkflowRun:
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
    validate_only: bool
    - whether to validate the workflow without queueing it

    Returns
    -------
    response: WorkflowRun
    - a workflow run object for the requested run_id
    """
    try:
        wf = Workflow.model_validate_json(workflow)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=422, detail=str(e)) from e

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

    wf_run = create_run(
        workflow=wf,
        workcell=workcell,
        experiment_id=experiment_id,
        payload=payload,
        simulate=simulate,
    )

    if not validate_only:
        wf_run = save_workflow_files(wf_run=wf_run, files=files)
        with state_manager.wc_state_lock():
            state_manager.set_workflow_run(wf_run)
    return wf_run


@router.get("/{run_id}")
def get_run(
    run_id: str,
) -> WorkflowRun:
    """Pulls the status of a workflow run

    Parameters
    ----------
    run_id : str
       The programmatically generated id of the workflow


    Returns
    -------
    response: WorkflowRun
        a WorkflowRun object for the requested run_id
    """
    try:
        with state_manager.wc_state_lock():
            workflow = state_manager.get_workflow_run(run_id)
        return workflow
    except KeyError as err:
        raise HTTPException(
            status_code=404, detail=f"Workflow run {run_id} not found"
        ) from err


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
