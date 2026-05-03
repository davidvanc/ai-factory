from fastapi import APIRouter, Query
from src.models import AnalyzeRequest, AnalyzeResponse, HealthResponse
from src.logic import analyze_text

router = APIRouter()

@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_post(request: AnalyzeRequest):
    result = analyze_text(request.text)
    return result

@router.get("/analyze", response_model=AnalyzeResponse)
def analyze_get(text: str = Query(..., min_length=1, description="De tekst om te analyseren")):
    result = analyze_text(text)
    return result

@router.get("/health", response_model=HealthResponse)
def health_check():
    return {"status": "ok"}
