"""
Router for the "workcells"/"wc" endpoints
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from wei.core.state_manager import StateManager
from wei.core.workcell import set_config_from_workcell
from wei.helpers import initialize_state
from wei.types import Workcell, WorkflowStatus
from wei.core.events import EventHandler
from wei.core.events import Event

import asyncio

import time

router = APIRouter()

state_manager = StateManager()


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
    with state_manager.state_lock():
        state_manager.set_workcell(workcell)
        set_config_from_workcell(workcell)
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

@router.websocket("/state/ws")
async def get_state(websocket: WebSocket) -> JSONResponse:
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
    print("start")
    EventHandler.log_event(Event(event_type="start", event_name="start"))
    await websocket.accept()
    EventHandler.log_event(Event(event_type="start", event_name="start"))
    print("test")
   
    # data = await websocket.receive_text()
    # EventHandler.log_event(Event(event_type="recieve", event_name=str(data)))
    await websocket.send_json(state_manager.get_state())
    while True: 
        if state_manager.has_state_changed():
            await websocket.send_json(state_manager.get_state())
        await asyncio.sleep(0.5)

    # while True: 
    #     try:
    #         EventHandler.log_event(Event(event_type="test", event_name="test"))
    #         print("send")
    #         test = await websocket.send_text({"hello world"})
    #         EventHandler.log_event(Event(event_type="test", event_name=str(test)))
            
    #         time.sleep(0.5)
    #     except WebSocketDisconnect:
    #         break
            
        

    


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
    with state_manager.state_lock():
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
