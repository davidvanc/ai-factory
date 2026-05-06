from fastapi import APIRouter, Query
from src.models import HashRequest, HashResponse, StatusResponse
from src.logic import calculate_md5
from src.service_template.logging_config import get_logger

log = get_logger("md5_routes")
router = APIRouter()

@router.post("/hash", response_model=HashResponse)
async def create_hash(request: HashRequest):
    log.info("Calculating MD5 for POST request")
    md5_hash = calculate_md5(request.text)
    return HashResponse(text=request.text, md5=md5_hash)

@router.get("/hash", response_model=HashResponse)
async def get_hash(text: str = Query(..., description="The text to hash")):
    log.info("Calculating MD5 for GET request")
    md5_hash = calculate_md5(text)
    return HashResponse(text=text, md5=md5_hash)

@router.get("/status", response_model=StatusResponse)
async def get_status():
    log.info("Status check requested")
    return StatusResponse(status="ok")
