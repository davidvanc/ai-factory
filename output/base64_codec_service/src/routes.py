from __future__ import annotations
import json
from typing import Type, TypeVar
from fastapi import APIRouter, Request, Response
from pydantic import BaseModel, ValidationError
from src import config
from src import errors
from src import logic
from src.errors import ApiError
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

router = APIRouter(tags=["codec"])
TModel = TypeVar("TModel", bound=BaseModel)

async def _parse_body(request: Request, model: Type[TModel]) -> TModel:
    raw_ct = request.headers.get("content-type", "")
    ct = raw_ct.split(";")[0].strip().lower()
    if ct != "application/json":
        raise errors.invalid_content_type(raw_ct if raw_ct else "<leeg>")
    body = await request.body()
    if len(body) > config.MAX_BODY_BYTES:
        raise errors.input_too_large(len(body), config.MAX_BODY_BYTES)
    try:
        payload = json.loads(body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise errors.invalid_json(str(exc))
    if not isinstance(payload, dict):
        raise ApiError(
            422,
            errors.INVALID_JSON,
            "De JSON-body moet een object zijn.",
            detail=f"Ontvangen type: {type(payload).__name__}.",
            position=None,
        )
    try:
        return model.model_validate(payload)
    except ValidationError as exc:
        raise errors.from_pydantic_error(exc)

@router.post(
    "/encode",
    response_model=EncodeResponse,
    responses={400: {"model": ErrorResponse}, 413: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
async def encode_endpoint(request: Request) -> Response:
    try:
        payload = await _parse_body(request, EncodeRequest)
        return logic.encode_text(payload.text, payload.url_safe, payload.encoding)
    except ApiError as exc:
        return errors.error_response(exc)

@router.post(
    "/decode",
    response_model=DecodeResponse,
    responses={400: {"model": ErrorResponse}, 413: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
async def decode_endpoint(request: Request) -> Response:
    try:
        payload = await _parse_body(request, DecodeRequest)
        return logic.decode_base64_to_text(payload.data, payload.encoding, payload.strict)
    except ApiError as exc:
        return errors.error_response(exc)

@router.post(
    "/validate",
    response_model=ValidateResponse,
    responses={413: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
async def validate_endpoint(request: Request) -> Response:
    try:
        payload = await _parse_body(request, ValidateRequest)
        return logic.validate_base64_string(payload.data)
    except ApiError as exc:
        return errors.error_response(exc)

@router.get("/status", response_model=StatusResponse)
async def status_endpoint() -> StatusResponse:
    return StatusResponse(
        status="ok",
        service=config.SERVICE_NAME,
        version=config.SERVICE_VERSION,
        supported_alphabets=config.SUPPORTED_ALPHABETS,
        max_input_bytes=config.MAX_INPUT_BYTES,
        counters=logic.get_counters(),
    )
