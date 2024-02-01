"""
Router for the "runs" endpoints
"""
from typing import Any, Dict, Optional

import yaml
from fastapi import APIRouter, UploadFile
from fastapi.responses import JSONResponse

from wei.core.data_classes import BaseModel, Workflow, WorkflowStatus
from wei.core.loggers import WEI_Logger
from wei.core.state_manager import StateManager
from wei.core.workflow import create_run

router = APIRouter()

state_manager = StateManager()


class StartRunParams(BaseModel):
    """JSON Body definition for the /runs/start endpoint"""

    experiment_id: str
    workflow: Workflow
    payload: Optional[Dict[str, Any]] = {}
    simulate: Optional[bool] = False


@router.post("/start")
async def start_run(params: StartRunParams) -> JSONResponse:
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
    wf = params.workflow
    logger = WEI_Logger.get_experiment_logger(params.experiment_id)
    logger.info(f"Received job run request: {wf.name}")
    workcell = state_manager.get_workcell()

    wf_run = create_run(
        wf, workcell, params.experiment_id, params.payload, params.simulate
    )

    with state_manager.state_lock():
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
        logger = WEI_Logger.get_experiment_logger(experiment_id)
        logger.info(f"Received job run request: {wf.name}")
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
        with state_manager.state_lock():
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

    wf_run = state_manager.get_workflow_run(run_id)
    with open(wf_run.run_log) as f:
        return f.read()
