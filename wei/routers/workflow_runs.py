"""
Router for the "runs" endpoints
"""
import json
import traceback

import yaml
from fastapi import APIRouter, UploadFile
from fastapi.responses import JSONResponse

from wei.core.data_classes import Workflow, WorkflowStatus
from wei.core.loggers import WEI_Logger
from wei.core.state_manager import StateManager
from wei.core.workflow import create_run

router = APIRouter()

state_manager = StateManager()


@router.post("/start")
async def start_run(
    experiment_id: str,
    workflow: UploadFile,
    payload: UploadFile,
    simulate: bool = False,
) -> JSONResponse:
    """
    parses the payload and workflow files, and then pushes a workflow job onto the redis queue

    Parameters
    ----------
    workflow: UploadFile
    - The workflow yaml file
    payload: UploadFile
    - The data input file to the workflow
    experiment_path: str
    - The path to the data of the experiment for the workflow
    simulate: bool
    - whether to use real robots or not

    Returns
    -------
    response: Dict
    - a dictionary including whether queueing succeeded, the jobs ahead, and the id
    """
    wf = None
    wf_run = None
    try:
        workflow_content = await workflow.read()
        workflow_content_str = workflow_content.decode("utf-8")
        wf = Workflow(**yaml.safe_load(workflow_content_str))
        payload_bytes = await payload.read()
        payload_dict = json.loads(payload_bytes)
        if payload_dict is None:
            payload_dict = {}
        logger = WEI_Logger.get_experiment_logger(experiment_id)
        logger.info(f"Received job run request: {wf.name}")
        workcell = state_manager.get_workcell()

        wf_run = create_run(wf, workcell, experiment_id, payload_dict, simulate)

        with state_manager.state_lock():
            state_manager.set_workflow_run(wf_run)
        return JSONResponse(
            content={
                "wf": wf_run.model_dump(mode="json"),
                "run_id": wf_run.run_id,
                "status": str(wf_run.status),
            }
        )
    except Exception as e:
        traceback.print_exc()
        if wf_run:
            return JSONResponse(
                status_code=500,
                content={
                    "wf": wf_run.model_dump(mode="json"),
                    "error": f"Error: {e}",
                    "status": str(WorkflowStatus.FAILED),
                },
            )
        elif wf:
            return JSONResponse(
                status_code=500,
                content={
                    "wf": wf.model_dump(mode="json"),
                    "error": f"Error: {e}",
                    "status": str(WorkflowStatus.FAILED),
                },
            )
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "error": f"Error: {e}",
                    "status": str(WorkflowStatus.FAILED),
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
