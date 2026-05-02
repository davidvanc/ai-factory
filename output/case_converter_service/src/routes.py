from fastapi import APIRouter, HTTPException
from src.models import (
    ConvertRequest, ConvertResponse, ConvertAllRequest, ConvertAllResponse,
    CasesResponse, StatusResponse
)
from src.logic import (
    convert_case, SUPPORTED_CASES, to_upper, to_lower, 
    to_title, to_snake, to_kebab, to_camel
)

router = APIRouter()

@router.post("/convert", response_model=ConvertResponse)
def convert_text(request: ConvertRequest):
    if request.target_case not in SUPPORTED_CASES:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid target_case. Supported cases are: {', '.join(SUPPORTED_CASES)}"
        )
    
    result = convert_case(request.text, request.target_case)
    return ConvertResponse(
        original=request.text,
        target_case=request.target_case,
        result=result
    )

@router.post("/convert/all", response_model=ConvertAllResponse)
def convert_all(request: ConvertAllRequest):
    return ConvertAllResponse(
        original=request.text,
        upper=to_upper(request.text),
        lower=to_lower(request.text),
        title=to_title(request.text),
        snake=to_snake(request.text),
        kebab=to_kebab(request.text),
        camel=to_camel(request.text)
    )

@router.get("/cases", response_model=CasesResponse)
def get_cases():
    return CasesResponse(supported_cases=SUPPORTED_CASES)

@router.get("/status", response_model=StatusResponse)
def get_status():
    return StatusResponse(status="ok", service="case_converter_service")
