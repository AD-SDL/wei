"""
Router for the "workcells"/"wc" endpoints
"""
import json

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse

from wei.core.data_classes import WorkflowStatus
from wei.core.state_manager import StateManager

router = APIRouter()

state_manager = StateManager()


@router.get("/state", response_class=HTMLResponse)
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
    with state_manager.state_lock():
        return JSONResponse(content={"wc_state": json.dumps(state_manager.get_state())})


@router.delete("/clear_runs")
async def clear_runs() -> JSONResponse:
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
    with state_manager.state_lock():
        for run_id, wf_run in state_manager.get_all_workflow_runs().items():
            if (
                wf_run.status == WorkflowStatus.COMPLETED
                or wf_run.status == WorkflowStatus.FAILED
            ):
                state_manager.delete_workflow_run(run_id)
        return JSONResponse(
            content={"Workflows": str(state_manager.get_all_workflow_runs())}
        )
