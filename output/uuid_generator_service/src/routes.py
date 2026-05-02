from fastapi import APIRouter
from src.models import GenerateResponse, GenerateBatchRequest, GenerateBatchResponse
from src.logic import generate_uuid, generate_uuids
from src.service_template.logging_config import get_logger

log = get_logger("uuid_routes")
router = APIRouter()

@router.post("/generate", response_model=GenerateResponse)
async def generate():
    log.info("Generating single UUID")
    new_uuid = generate_uuid()
    return GenerateResponse(uuid=new_uuid)

@router.post("/generate-batch", response_model=GenerateBatchResponse)
async def generate_batch(request: GenerateBatchRequest):
    log.info(f"Generating batch of {request.count} UUIDs")
    uuids = generate_uuids(request.count)
    return GenerateBatchResponse(uuids=uuids, count=request.count)
