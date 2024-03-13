"""
Router for the modules endpoints
"""

from typing import Union

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from wei.core.state_manager import StateManager

router = APIRouter()

state_manager = StateManager()


@router.get("/{module_name}/state", response_model=None)
def get_module(
    module_name: str,
) -> Union[JSONResponse, HTTPException]:
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
