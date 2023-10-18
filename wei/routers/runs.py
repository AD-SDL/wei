"""
Router for the "runs" endpoints
"""
import json
import os
import re
from pathlib import Path

import yaml
from fastapi import APIRouter, File, Request, UploadFile
from fastapi.responses import JSONResponse

from wei.core.data_classes import WorkflowRun, WorkflowStatus
from wei.core.loggers import WEI_Logger
from wei.core.workflow import WorkflowRunner

router = APIRouter()


@router.post("/start")
async def start_run(
    request: Request,
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
    state_manager = request.app.state_manager
    try:
        log_dir = Path(experiment_path)
        wf = WorkflowRun(
            name=Path(workflow.filename).name.split(".")[0],
            modules=[],
            flowdef=[],
            experiment_path=str(log_dir),
        )
        wf.label = wf.name
        wf.run_dir = str(Path(log_dir, "runs", f"{wf.name}_{wf.run_id}"))
        experiment_id = log_dir.name.split("_")[-1]
        logger = WEI_Logger.get_logger("log_" + experiment_id, log_dir)
        logger.info("Received job run request")

        workflow_content = await workflow.read()
        payload = await payload.read()
        # Decode the bytes object to a string
        workflow_content_str = workflow_content.decode("utf-8")
        wf.payload = json.loads(payload)
        workflow_runner = WorkflowRunner(
            workflow_def=yaml.safe_load(workflow_content_str),
            workcell=state_manager.get_workcell(),
            payload=wf.payload,
            experiment_path=str(experiment_path),
            run_id=wf.run_id,
            simulate=simulate,
            workflow_name=wf.name,
        )

        flowdef = []

        for step in workflow_runner.steps:
            flowdef.append(
                {
                    "step": json.loads(step["step"].json()),
                    "locations": step["locations"],
                }
            )
        wf.flowdef = flowdef
        with state_manager.state_lock():
            state_manager.set_workflow_run(wf.run_id, wf)
    except Exception as e:  # noqa
        print(e)
        wf.status = WorkflowStatus.FAILED
        wf.hist["validation"] = f"Error: {e}"
        with state_manager.state_lock():
            state_manager.set_workflow_run(wf.run_id, wf)
    return JSONResponse(
        content={
            "wf": wf.model_dump(mode="json"),
            "run_id": wf.run_id,
            "status": str(wf.status),
        }
    )


@router.get("/{run_id}/state")
def get_run_status(run_id: str, request: Request) -> JSONResponse:
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
    state_manager = request.app.state_manager
    try:
        with state_manager.state_lock():
            workflow = state_manager.get_workflow_run(run_id)
        return JSONResponse(content=workflow.model_dump(mode="json"))
    except KeyError:
        return JSONResponse(content={"status": WorkflowStatus.UNKNOWN})


@router.get("/{run_id}/log")
async def log_run_return(run_id: str, experiment_path: str) -> str:
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
        if re.match(".*" + run_id, file):
            with open(log_dir / "wei_runs" / file / "runLogger.log") as f:
                return f.read()
