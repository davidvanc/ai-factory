from fastapi import APIRouter, HTTPException, Query, Request
from typing import Optional
from src.models import (
    ToRomanRequest, ToRomanResponse,
    ToIntegerRequest, ToIntegerResponse,
    ConvertResponse, StatusResponse
)
from src.logic import int_to_roman, roman_to_int

router = APIRouter()

@router.post("/to-roman", response_model=ToRomanResponse)
def to_roman(request: ToRomanRequest):
    try:
        roman = int_to_roman(request.number)
        return ToRomanResponse(number=request.number, roman=roman)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

@router.post("/to-integer", response_model=ToIntegerResponse)
def to_integer(request: ToIntegerRequest):
    try:
        number = roman_to_int(request.roman)
        return ToIntegerResponse(roman=request.roman.upper(), number=number)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

@router.get("/convert", response_model=ConvertResponse)
async def convert(request: Request, number: Optional[int] = Query(None), roman: Optional[str] = Query(None)):
    if number is None and roman is None:
        try:
            body = await request.json()
            if isinstance(body, dict):
                if "number" in body:
                    number = int(body["number"])
                if "roman" in body:
                    roman = str(body["roman"])
        except Exception:
            pass

    if number is not None and roman is None:
        if not isinstance(number, int) or not (1 <= number <= 3999):
            raise HTTPException(status_code=422, detail="Number must be between 1 and 3999")
        try:
            roman_str = int_to_roman(number)
            return ConvertResponse(number=number, roman=roman_str)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
    elif roman is not None and number is None:
        try:
            num = roman_to_int(roman)
            return ConvertResponse(number=num, roman=roman.upper())
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
    else:
        raise HTTPException(status_code=422, detail="Provide exactly one of 'number' or 'roman' query parameters")

@router.get("/status", response_model=StatusResponse)
def status():
    return StatusResponse(status="ok", min=1, max=3999)
