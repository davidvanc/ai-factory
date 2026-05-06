from fastapi import APIRouter
from pydantic import BaseModel, StrictStr
from src.logic import reverse_string

router = APIRouter()

class ReverseRequest(BaseModel):
    text: StrictStr

class ReverseResponse(BaseModel):
    reversed: str

@router.post("/reverse", response_model=ReverseResponse, description="Keert de gegeven string om en retourneert het resultaat")
async def reverse_text(request: ReverseRequest):
    reversed_text = reverse_string(request.text)
    return ReverseResponse(reversed=reversed_text)
