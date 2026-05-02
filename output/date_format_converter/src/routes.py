from fastapi import APIRouter, HTTPException
from src.models import (
    ConvertRequest, ConvertResponse, 
    DetectRequest, DetectResponse, 
    FormatsResponse, FormatItem, 
    StatusResponse
)
from src.logic import parse_date, format_date, detect_format

router = APIRouter()

@router.post("/convert", response_model=ConvertResponse)
def convert_date(req: ConvertRequest):
    try:
        dt = parse_date(req.value, req.from_format.value)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
        
    try:
        converted = format_date(dt, req.to_format.value)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    return ConvertResponse(
        original=req.value,
        converted=converted,
        from_format=req.from_format,
        to_format=req.to_format
    )

@router.post("/detect", response_model=DetectResponse)
def detect_date(req: DetectRequest):
    try:
        fmt = detect_format(req.value)
        return DetectResponse(value=req.value, detected_format=fmt)
    except ValueError:
        raise HTTPException(status_code=400, detail="Unrecognized date format")

@router.get("/formats", response_model=FormatsResponse)
def get_formats():
    return FormatsResponse(formats=[
        FormatItem(key="iso", example="2023-12-25"),
        FormatItem(key="eu", example="25-12-2023"),
        FormatItem(key="us", example="12/25/2023"),
        FormatItem(key="unix", example="1703462400")
    ])

@router.get("/status", response_model=StatusResponse)
def get_status():
    return StatusResponse(status="ok")

@router.get("/health", response_model=StatusResponse)
def get_health():
    return StatusResponse(status="ok")
