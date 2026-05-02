from fastapi import APIRouter, HTTPException, Query, Request
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
async def convert_get(request: Request, value: str = Query(None, description="Number to convert")):
    if value is None:
        try:
            body = await request.json()
            value = body.get("value", "0")
        except Exception:
            value = "0"
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
