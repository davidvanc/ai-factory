from fastapi import APIRouter, HTTPException, Query
from src.models import (
    ToRomanRequest, ToRomanResponse,
    ToIntegerRequest, ToIntegerResponse,
    ConvertResponse, StatusResponse
)
from src.logic import int_to_roman, roman_to_int

router = APIRouter()

@router.post("/to-roman", response_model=ToRomanResponse)
async def to_roman(request: ToRomanRequest):
    try:
        roman = int_to_roman(request.number)
        return ToRomanResponse(number=request.number, roman=roman)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

@router.post("/to-integer", response_model=ToIntegerResponse)
async def to_integer(request: ToIntegerRequest):
    try:
        number = roman_to_int(request.roman)
        return ToIntegerResponse(roman=request.roman, number=number)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

@router.get("/convert", response_model=ConvertResponse)
async def convert(value: str = Query("XLII", description="Integer or Roman numeral")):
    if value.lstrip('-').isdigit():
        num = int(value)
        try:
            roman = int_to_roman(num)
            return ConvertResponse(
                input=value,
                input_type="integer",
                output=roman,
                output_type="roman"
            )
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
    else:
        try:
            number = roman_to_int(value)
            return ConvertResponse(
                input=value,
                input_type="roman",
                output=number,
                output_type="integer"
            )
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))

@router.get("/status", response_model=StatusResponse)
async def status():
    return StatusResponse(
        status="ok",
        service="roman_numeral_converter",
        range="1-3999"
    )
