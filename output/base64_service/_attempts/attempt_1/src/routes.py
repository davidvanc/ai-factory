from __future__ import annotations
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from src.errors import Base64ServiceError
from src.logic import decode_data, encode_text
from src.models import (
    DecodeRequest,
    DecodeResponse,
    EncodeRequest,
    EncodeResponse,
    StatusResponse,
)

router = APIRouter(tags=["base64"])


@router.post("/encode", response_model=EncodeResponse, status_code=200, summary="Encodeer tekst naar base64")
def encode_endpoint(payload: EncodeRequest) -> EncodeResponse | JSONResponse:
    try:
        encoded, padding_stripped = encode_text(payload.text, url_safe=payload.url_safe, strip_padding=payload.strip_padding)
    except Base64ServiceError as exc:
        return exc.to_response()
    return EncodeResponse(
        encoded=encoded,
        input_length=len(payload.text),
        output_length=len(encoded),
        url_safe=payload.url_safe,
        padding_stripped=padding_stripped,
    )


@router.post("/decode", response_model=DecodeResponse, status_code=200, summary="Decodeer base64 naar tekst")
def decode_endpoint(payload: DecodeRequest) -> DecodeResponse | JSONResponse:
    try:
        decoded, padding_added = decode_data(payload.data, url_safe=payload.url_safe)
    except Base64ServiceError as exc:
        return exc.to_response()
    return DecodeResponse(
        decoded=decoded,
        input_length=len(payload.data),
        output_length=len(decoded),
        url_safe=payload.url_safe,
        padding_added=padding_added,
    )


@router.get("/status", response_model=StatusResponse, status_code=200, summary="Healthcheck en servicemetadata")
def status_endpoint() -> StatusResponse:
    return StatusResponse()


__all__ = ["router"]
