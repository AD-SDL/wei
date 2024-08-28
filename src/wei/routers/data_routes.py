"""
Router for the "data" endpoints
"""

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Form, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from typing_extensions import Annotated

from wei.core.state_manager import state_manager
from wei.core.storage import get_experiment_directory
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


@router.post("/")
async def create_datapoint(
    datapoint: Annotated[str, Form()], file: Optional[UploadFile] = None
) -> JSONResponse:
    """Allows users to create datapoints as needed."""
    datapoint = DataPoint.model_validate_json(datapoint)
    if datapoint.experiment_id is None:
        return JSONResponse(
            {
                "status": "error",
                "message": "Experiment ID is required when uploading datapoints.",
            },
            status_code=400,
        )
    if file and datapoint.type == "local_file":
        experiment_directory = get_experiment_directory(datapoint.experiment_id)
        datapoint.path = experiment_directory / (
            datapoint.id + Path(datapoint.path).suffix
        )
        with open(datapoint.path, "wb") as f:
            contents = file.file.read()
            f.write(contents)
    state_manager.set_datapoint(datapoint=datapoint)
    return JSONResponse({"status": "success"})
