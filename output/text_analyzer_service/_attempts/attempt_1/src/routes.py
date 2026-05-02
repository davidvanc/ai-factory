from fastapi import APIRouter, Query
from src.models import AnalyzeRequest, AnalyzeResponse, StatusResponse
from src.logic import analyze_text

router = APIRouter()

@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_post(request: AnalyzeRequest):
    return analyze_text(request.text)

@router.get("/analyze", response_model=AnalyzeResponse)
def analyze_get(text: str = Query(..., description="Text to analyze")):
    return analyze_text(text)

@router.get("/status", response_model=StatusResponse)
def get_status():
    return {"status": "ok", "service": "text_analyzer_service"}

@router.get("/health")
def get_health():
    return {"status": "ok"}
