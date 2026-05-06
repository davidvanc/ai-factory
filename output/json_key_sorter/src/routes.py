from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Dict, Any, List
from src.logic import sort_dict_recursive
from src.service_template.logging_config import get_logger

log = get_logger("routes")
router = APIRouter()

class SortRequest(BaseModel):
    data: Dict[str, Any] = Field(..., description="The JSON object to sort")

class SortResponse(BaseModel):
    sorted: Dict[str, Any]
    keys: List[str]

@router.post("/sort-keys", response_model=SortResponse)
async def sort_keys_endpoint(request: SortRequest):
    log.info("Received request to sort keys")
    sorted_data = sort_dict_recursive(request.data)
    return SortResponse(
        sorted=sorted_data,
        keys=list(sorted_data.keys())
    )
