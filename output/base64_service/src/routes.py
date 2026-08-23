from fastapi import APIRouter
from fastapi.responses import JSONResponse
from src.errors import Base64Error, error_payload
from src.logic import decode_data, encode_text, service_status, validate_data
from src.models import (
    DecodeRequest,
    DecodeResponse,
    EncodeRequest,
    EncodeResponse,
    ErrorResponse,
    StatusResponse,
    ValidateRequest,
    ValidateResponse,
)

router = APIRouter()


@router.post(
    "/encode",
    response_model=EncodeResponse,
    responses={422: {"model": ErrorResponse}},
)
def encode_endpoint(payload: EncodeRequest):
    try:
        result = encode_text(
            payload.text,
            url_safe=payload.url_safe,
            strip_padding=payload.strip_padding,
        )
        return EncodeResponse(**result)
    except Base64Error as exc:
        return JSONResponse(status_code=422, content=error_payload(exc))


@router.post(
    "/decode",
    response_model=DecodeResponse,
    responses={422: {"model": ErrorResponse}},
)
def decode_endpoint(payload: DecodeRequest):
    try:
        result = decode_data(
            payload.data,
            url_safe=payload.url_safe,
            fix_padding=payload.fix_padding,
        )
        return DecodeResponse(**result)
    except Base64Error as exc:
        return JSONResponse(status_code=422, content=error_payload(exc))


@router.post("/validate", response_model=ValidateResponse)
def validate_endpoint(payload: ValidateRequest):
    result = validate_data(payload.data)
    return ValidateResponse(**result)


@router.get("/status", response_model=StatusResponse)
def status_endpoint():
    return StatusResponse(**service_status())
