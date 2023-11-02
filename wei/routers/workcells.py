"""
Router for the "workcells"/"wc" endpoints
"""
import json

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse

from wei.core.config import Config
from wei.core.data_classes import WorkflowStatus

router = APIRouter()

state_manager = Config.state_manager


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
        wc_state = json.loads(state_manager.get_state())
    return JSONResponse(
        content={"wc_state": json.dumps(wc_state)}
    )  # templates.TemplateResponse("item.html", {"request": request, "wc_state": wc_state})


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
        for workflow in state_manager.get_all_workflow_runs():
            if (
                workflow.status == WorkflowStatus.COMPLETED
                or workflow.status == WorkflowStatus.FAILED
            ):
                state_manager.delete_workflow_run(workflow.run_id)
        return JSONResponse(
            content={"Workflows": str(state_manager.get_all_workflow_runs())}
        )
