from fastapi import APIRouter, Query, HTTPException
from pydantic import ValidationError
from src.models import ConvertRequest, ConvertResponse
from src.logic import process_hex_color

router = APIRouter()

@router.post("/convert", response_model=ConvertResponse)
def convert_post(request: ConvertRequest):
    return process_hex_color(request.hex)

@router.get("/convert", response_model=ConvertResponse)
def convert_get(hex: str = Query("FF5733", description="HEX color code")):
    try:
        req = ConvertRequest(hex=hex)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())
    return process_hex_color(req.hex)
