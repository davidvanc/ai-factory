from fastapi import APIRouter
from pydantic import BaseModel, StrictStr
from src.logic import reverse_string
from src.service_template.logging_config import get_logger

log = get_logger("reverse_routes")

router = APIRouter()

class ReverseRequest(BaseModel):
    text: StrictStr

class ReverseResponse(BaseModel):
    reversed: str

@router.post("/reverse", response_model=ReverseResponse, description="Keert de meegegeven string om en geeft het resultaat terug")
async def reverse_endpoint(request: ReverseRequest):
    log.info("Received request to reverse string")
    reversed_text = reverse_string(request.text)
    return ReverseResponse(reversed=reversed_text)
