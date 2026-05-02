from fastapi import APIRouter, HTTPException, Query
from src.models import ConvertRequest, ConvertResponse
from src.logic import number_to_nl_text

router = APIRouter()

@router.post("/convert", response_model=ConvertResponse)
def convert_post(request: ConvertRequest):
    try:
        text = number_to_nl_text(request.value)
        return ConvertResponse(value=request.value, text=text)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid number format")

@router.get("/convert", response_model=ConvertResponse)
def convert_get(value: str = Query(..., description="Number to convert")):
    try:
        text = number_to_nl_text(value)
        return ConvertResponse(value=value, text=text)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid number format")

@router.get("/status")
def status():
    return {"status": "ok"}

@router.get("/health")
def health():
    return {"status": "ok"}
