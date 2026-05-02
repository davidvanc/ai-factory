from fastapi import APIRouter, Query
from src.models import ConvertRequest, ConvertResponse, StatusResponse, HealthResponse
from src.logic import number_to_french

router = APIRouter()

@router.post("/convert", response_model=ConvertResponse)
def convert_post(request: ConvertRequest):
    text = number_to_french(request.number)
    return ConvertResponse(number=request.number, text=text)

@router.get("/convert", response_model=ConvertResponse)
def convert_get(number: int = Query(0, ge=0, le=1000000000000000)):
    text = number_to_french(number)
    return ConvertResponse(number=number, text=text)

@router.get("/status", response_model=StatusResponse)
def status():
    return StatusResponse(status="ok", range="0 to 1000000000000000")

@router.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok")
