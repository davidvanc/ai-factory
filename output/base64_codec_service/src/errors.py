from __future__ import annotations
import json
from typing import Any, Dict, List, Optional
from fastapi.responses import JSONResponse
from pydantic import ValidationError

EMPTY_INPUT = "EMPTY_INPUT"
MISSING_FIELD = "MISSING_FIELD"
VALIDATION_ERROR = "VALIDATION_ERROR"
INVALID_JSON = "INVALID_JSON"
INVALID_CONTENT_TYPE = "INVALID_CONTENT_TYPE"
INPUT_TOO_LARGE = "INPUT_TOO_LARGE"
UNSUPPORTED_ENCODING = "UNSUPPORTED_ENCODING"
NOT_ENCODABLE_TEXT = "NOT_ENCODABLE_TEXT"
NOT_DECODABLE_TEXT = "NOT_DECODABLE_TEXT"
INVALID_BASE64_CHARACTER = "INVALID_BASE64_CHARACTER"
INVALID_PADDING = "INVALID_PADDING"
MIXED_ALPHABET = "MIXED_ALPHABET"
DECODE_FAILED = "DECODE_FAILED"

class ApiError(Exception):
    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        detail: Optional[str] = None,
        position: Optional[int] = None,
    ) -> None:
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.detail = detail
        self.position = position
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_code": self.error_code,
            "message": self.message,
            "detail": self.detail,
            "position": self.position,
        }

    def to_response(self) -> JSONResponse:
        return JSONResponse(status_code=self.status_code, content=self.to_dict())

def error_response(exc: ApiError) -> JSONResponse:
    return exc.to_response()

def empty_input(field: str) -> ApiError:
    return ApiError(
        422,
        EMPTY_INPUT,
        f"Veld '{field}' mag niet leeg zijn.",
        detail=f"Geef een niet-lege string mee in veld '{field}'.",
        position=None,
    )

def missing_field(field: str, detail: Optional[str] = None) -> ApiError:
    if detail is None:
        detail = f"Veld '{field}' is verplicht en moet een string zijn."
    return ApiError(
        422,
        MISSING_FIELD,
        f"Verplicht veld '{field}' ontbreekt of is null.",
        detail=detail,
        position=None,
    )

def validation_error(field: str, reason: str, detail: Optional[str] = None) -> ApiError:
    return ApiError(
        422,
        VALIDATION_ERROR,
        f"Ongeldige waarde voor veld '{field}': {reason}.",
        detail=detail,
        position=None,
    )

def invalid_json(reason: str) -> ApiError:
    return ApiError(
        422,
        INVALID_JSON,
        "De request-body is geen geldige JSON.",
        detail=reason,
        position=None,
    )

def invalid_content_type(received: str) -> ApiError:
    return ApiError(
        422,
        INVALID_CONTENT_TYPE,
        "Content-Type moet 'application/json' zijn.",
        detail=f"Ontvangen Content-Type: '{received}'.",
        position=None,
    )

def input_too_large(actual_bytes: int, limit_bytes: int) -> ApiError:
    return ApiError(
        413,
        INPUT_TOO_LARGE,
        f"Invoer is {actual_bytes} bytes; maximaal {limit_bytes} bytes toegestaan.",
        detail=f"Verklein de invoer tot maximaal {limit_bytes} bytes.",
        position=None,
    )

def unsupported_encoding(encoding: str, supported: List[str]) -> ApiError:
    return ApiError(
        422,
        UNSUPPORTED_ENCODING,
        f"Tekstencoding '{encoding}' wordt niet ondersteund.",
        detail="Ondersteunde encodings: " + ", ".join(supported) + ".",
        position=None,
    )

def from_pydantic_error(exc: ValidationError) -> ApiError:
    errs = exc.errors()
    first_err = errs[0]
    loc = first_err.get("loc", ())
    if loc:
        field = ".".join(str(p) for p in loc)
    else:
        field = "body"
    detail_list = [
        {
            "field": ".".join(str(p) for p in e.get("loc", ())) or "body",
            "type": e["type"],
            "message": e["msg"],
        }
        for e in errs
    ]
    detail = json.dumps(detail_list, ensure_ascii=False)
    if first_err["type"] == "missing":
        return missing_field(field, detail=detail)
    else:
        return validation_error(field, first_err["msg"], detail=detail)
