"""
Router for the "locations" endpoints
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/states")
def show_states(request: Request) -> JSONResponse:
    """

    Describes the state of the workcell locations

    Parameters
    ----------
    None

     Returns
    -------
     response: Dict
       the state of the workcell locations, with the id of the run that last filled the location
    """

    state_manager = request.app.state_manager

    with state_manager.state_lock():
        return JSONResponse(
            content={
                "location_states": {
                    location_name: location.model_dump(mode="json")
                    for location_name, location in state_manager.get_all_locations().items()
                }
            }
        )


@router.get("/{location}/state")
def loc(location: str, request: Request) -> JSONResponse:
    """

    Describes the state of the workcell locations
    Parameters
    ----------
    None

     Returns
    -------
     response: Dict
       the state of the workcell locations, with the id of the run that last filled the location
    """
    state_manager = request.app.state_manager

    try:
        with state_manager.state_lock():
            return JSONResponse(
                content={
                    str(location): str(
                        state_manager.get_location(location).model_dump(mode="json")
                    )
                }
            )
    except KeyError:
        return HTTPException(status_code=404, detail="Location not found")


@router.post("/{location_name}/set")
async def update(
    location_name: str, experiment_id: str, request: Request
) -> JSONResponse:
    """
    Manually update the state of a location in the workcell.
    Parameters
    ----------
    location: the name of the location to update
    experiment_id: the id of the experiment that is in the location

    Returns
    -------
        response: Dict
         the state of the workcell locations, with the id of the run that last filled the location
    """
    state_manager = request.app.state_manager

    def update_location_state(location: dict, value: str) -> dict:
        location["state"] = "Empty"
        return location

    with state_manager.state_lock():
        if experiment_id == "":
            state_manager.update_location(location_name, update_location_state, "Empty")
        else:
            state_manager.update_location(
                location_name, update_location_state, experiment_id
            )
        return JSONResponse(
            content={
                "Locations": {
                    location_name: location.model_dump(mode="json")
                    for location_name, location in state_manager.get_all_locations().items()
                }
            }
        )
