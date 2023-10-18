"""
Router for the modules endpoints
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/{module_name}/state")
def mod(module_name: str, request: Request) -> JSONResponse:
    """
    Gets the state of a given module
    Parameters
    ----------
    module_name: the name of the module to get the state of

     Returns
    -------
     response: Dict
       the state of the requested module
    """
    state_manager = request.app.state_manager

    try:
        with state_manager.state_lock():
            return JSONResponse(
                content={
                    str(module_name): state_manager.get_module(module_name).model_dump(
                        mode="json"
                    )
                }
            )
    except KeyError:
        return HTTPException(status_code=404, detail="Module not found")
