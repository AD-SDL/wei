"""
Router for the "workcells"/"wc" endpoints
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from wei.config import Config
from wei.core.state_manager import state_manager
from wei.core.workcell import set_config_from_workcell
from wei.types import Workcell, WorkflowStatus
from wei.utils import initialize_state

router = APIRouter()


@router.post("/", response_class=JSONResponse)
def set_workcell(workcell: Workcell) -> JSONResponse:
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
    with state_manager.wc_state_lock():
        state_manager.set_workcell(workcell)
        set_config_from_workcell(workcell)
        return JSONResponse(
            content=state_manager.get_workcell().model_dump(mode="json")
        )


@router.get("/")
def get_workcell() -> Workcell:
    """

    Describes the workcell's state

    Parameters
    ----------
    None

     Returns
    -------
     response: Dict
       the definition of the workcell
    """
    with state_manager.wc_state_lock():
        return state_manager.get_workcell().model_dump(mode="json")


@router.get("/config")
def get_workcell_config() -> JSONResponse:
    """Returns the server configuration (including values set/overridden by cli args)"""
    return JSONResponse(Config.dump_to_json())


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
    with state_manager.wc_state_lock():
        return JSONResponse(content=state_manager.get_state())


@router.post("/state/reset", response_class=JSONResponse)
def reset_state() -> JSONResponse:
    """

    Resets the workcell's state

    Parameters
    ----------
    None

     Returns
    -------
     response: Dict
       the state of the workcell
    """
    with state_manager.wc_state_lock():
        state_manager.clear_state()
        initialize_state()
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
    with state_manager.wc_state_lock():
        for run_id, wf_run in state_manager.get_all_workflow_runs().items():
            if (
                wf_run.status == WorkflowStatus.COMPLETED
                or wf_run.status == WorkflowStatus.FAILED
            ):
                state_manager.delete_workflow_run(run_id)
        return JSONResponse(
            content={"Workflows": str(state_manager.get_all_workflow_runs())}
        )
