"""
Router for the "workcells"/"wc" endpoints
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from wei.core.data_classes import WorkcellData, WorkflowStatus
from wei.core.state_manager import StateManager

router = APIRouter()

state_manager = StateManager()


@router.post("/", response_class=JSONResponse)
def set_workcell(workcell: WorkcellData) -> JSONResponse:
    """

    Sets the workcell's state

    Parameters
    ----------
    None

     Returns
    -------
     response: Dict
       the state of the workcell
    """
    with state_manager.state_lock():
        state_manager.set_workcell(workcell)
        return JSONResponse(
            content=state_manager.get_workcell().model_dump(mode="json")
        )


@router.get("/state", response_class=JSONResponse)
def get_state() -> JSONResponse:
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
        return JSONResponse(content=state_manager.get_state())


@router.post("/state/clear", response_class=JSONResponse)
def clear_state() -> JSONResponse:
    """

    Clears the workcell's state

    Parameters
    ----------
    None

     Returns
    -------
     response: Dict
       the state of the workcell
    """
    with state_manager.state_lock():
        state_manager.clear_state()
        return JSONResponse(content=state_manager.get_state())


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
