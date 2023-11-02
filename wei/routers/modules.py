"""
Router for the modules endpoints
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from wei.config import Config

router = APIRouter()

state_manager = Config.state_manager


@router.get("/{module_name}/state")
def mod(
    module_name: str,
) -> JSONResponse:
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
