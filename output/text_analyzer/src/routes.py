from fastapi import APIRouter, Query
from src.models import AnalyzeRequest, AnalyzeResponse, StatusResponse
from src.logic import analyze_text

router = APIRouter()

@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_post(request: AnalyzeRequest):
    result = analyze_text(request.text)
    return AnalyzeResponse(**result)

@router.get("/analyze", response_model=AnalyzeResponse)
def analyze_get(text: str = Query(..., description="Text to analyze")):
    result = analyze_text(text)
    return AnalyzeResponse(**result)

@router.get("/status", response_model=StatusResponse)
def get_status():
    return StatusResponse(status="ok")

@router.get("/health", response_model=StatusResponse)
def get_health():
    return StatusResponse(status="ok")
