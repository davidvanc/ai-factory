from fastapi import APIRouter, HTTPException
from src.models import TemperatureRequest, ConversionRequest, ConversionResponse, StatusResponse
from src.logic import celsius_to_fahrenheit, fahrenheit_to_celsius

router = APIRouter()

@router.post("/convert/celsius-to-fahrenheit", response_model=ConversionResponse)
def convert_c2f(request: TemperatureRequest):
    output = celsius_to_fahrenheit(request.value)
    return ConversionResponse(
        input=request.value,
        input_unit="Celsius",
        output=output,
        output_unit="Fahrenheit"
    )

@router.post("/convert/fahrenheit-to-celsius", response_model=ConversionResponse)
def convert_f2c(request: TemperatureRequest):
    output = fahrenheit_to_celsius(request.value)
    return ConversionResponse(
        input=request.value,
        input_unit="Fahrenheit",
        output=output,
        output_unit="Celsius"
    )

@router.post("/convert", response_model=ConversionResponse)
def convert_any(request: ConversionRequest):
    if request.from_unit == request.to_unit:
        output = request.value
    elif request.from_unit == 'C' and request.to_unit == 'F':
        output = celsius_to_fahrenheit(request.value)
    elif request.from_unit == 'F' and request.to_unit == 'C':
        output = fahrenheit_to_celsius(request.value)
    else:
        raise HTTPException(status_code=400, detail="Invalid conversion units")

    return ConversionResponse(
        input=request.value,
        input_unit=request.from_unit,
        output=output,
        output_unit=request.to_unit
    )

@router.get("/status", response_model=StatusResponse)
def get_status():
    return StatusResponse(status="ok", service="temperature_converter")
