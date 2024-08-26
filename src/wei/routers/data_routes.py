"""
Router for the "data" endpoints
"""

from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse

from wei.core.state_manager import state_manager
from wei.types.datapoint_types import DataPoint

router = APIRouter()


@router.get("/{datapoint_id}")
async def get_datapoint(datapoint_id: str):
    """Returns a specific data point's value."""
    datapoint = state_manager.get_datapoint(datapoint_id)
    if datapoint.type == "local_file":
        return FileResponse(datapoint.path)
    else:
        return JSONResponse({"value": datapoint.value})


@router.get("/{datapoint_id}/info")
async def get_datapoint_info(datapoint_id: str) -> DataPoint:
    """Returns metadata about a specific data point."""
    datapoint = state_manager.get_datapoint(datapoint_id)
    return datapoint
