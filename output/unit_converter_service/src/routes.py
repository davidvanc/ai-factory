from fastapi import APIRouter, HTTPException
from src.models import ConversionRequest, ConversionResponse
from src.logic import convert_length, convert_weight, convert_temperature
from src.service_template.logging_config import get_logger

log = get_logger("unit_converter")
router = APIRouter(prefix="/convert", tags=["convert"])

@router.post("/length", response_model=ConversionResponse)
async def convert_length_endpoint(request: ConversionRequest):
    try:
        result = convert_length(request.value, request.from_unit, request.to_unit)
        return ConversionResponse(
            from_unit=request.from_unit,
            to_unit=request.to_unit,
            result=result
        )
    except ValueError:
        log.warning(f"Invalid length unit: {request.from_unit} or {request.to_unit}")
        raise HTTPException(status_code=422, detail="Invalid unit for length conversion")

@router.post("/weight", response_model=ConversionResponse)
async def convert_weight_endpoint(request: ConversionRequest):
    try:
        result = convert_weight(request.value, request.from_unit, request.to_unit)
        return ConversionResponse(
            from_unit=request.from_unit,
            to_unit=request.to_unit,
            result=result
        )
    except ValueError:
        log.warning(f"Invalid weight unit: {request.from_unit} or {request.to_unit}")
        raise HTTPException(status_code=422, detail="Invalid unit for weight conversion")

@router.post("/temperature", response_model=ConversionResponse)
async def convert_temperature_endpoint(request: ConversionRequest):
    try:
        result = convert_temperature(request.value, request.from_unit, request.to_unit)
        return ConversionResponse(
            from_unit=request.from_unit,
            to_unit=request.to_unit,
            result=result
        )
    except ValueError:
        log.warning(f"Invalid temperature unit: {request.from_unit} or {request.to_unit}")
        raise HTTPException(status_code=422, detail="Invalid unit for temperature conversion")
