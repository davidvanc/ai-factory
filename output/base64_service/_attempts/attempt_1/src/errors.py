from __future__ import annotations
from typing import Any, Dict
from fastapi.responses import JSONResponse


class Base64ServiceError(Exception):
    def __init__(self, error: str, message: str, detail: str, status_code: int) -> None:
        self.error = error
        self.message = message
        self.detail = detail
        self.status_code = status_code
        super().__init__(message)

    def to_payload(self) -> Dict[str, Any]:
        return {"error": self.error, "message": self.message, "detail": self.detail}

    def to_response(self) -> JSONResponse:
        return JSONResponse(status_code=self.status_code, content=self.to_payload())


class InputTooLargeError(Base64ServiceError):
    def __init__(self, size: int, limit: int) -> None:
        self.size = size
        self.limit = limit
        super().__init__(
            error="input_too_large",
            message=f"Invoer is te groot: {size} bytes, maximum is {limit} bytes.",
            detail=f"De limiet voor invoer is {limit} bytes. Verklein de invoer tot maximaal {limit} bytes en probeer opnieuw.",
            status_code=413,
        )


class InvalidBase64CharacterError(Base64ServiceError):
    def __init__(self, character: str, position: int, url_safe: bool) -> None:
        self.character = character
        self.position = position
        self.url_safe = url_safe
        if url_safe:
            allowed = "A-Z, a-z, 0-9, '-', '_' en '=' als padding"
        else:
            allowed = "A-Z, a-z, 0-9, '+', '/' en '=' als padding"
        super().__init__(
            error="invalid_base64_character",
            message=f"ongeldige base64: teken '{character}' op positie {position} is niet toegestaan.",
            detail=f"Toegestane tekens zijn {allowed}. Het eerste ongeldige teken staat op positie {position} (0-gebaseerd).",
            status_code=422,
        )


class InvalidBase64LengthError(Base64ServiceError):
    def __init__(self, length: int) -> None:
        self.length = length
        super().__init__(
            error="invalid_base64_length",
            message=f"ongeldige base64: lengte {length} kan niet gedecodeerd worden.",
            detail=(
                f"Een base64-string moet, na het automatisch aanvullen van '=' padding, een lengte hebben die "
                f"deelbaar is door 4. Bij lengte {length} blijft er 1 teken over ({length} % 4 == 1) en dat is "
                "nooit geldige base64. Verwijder of vul een teken aan."
            ),
            status_code=422,
        )


class Base64DecodeFailedError(Base64ServiceError):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(
            error="invalid_base64",
            message="ongeldige base64: de invoer kon niet gedecodeerd worden.",
            detail=f"De base64-decoder gaf de volgende melding: {reason}",
            status_code=422,
        )


class NonUtf8PayloadError(Base64ServiceError):
    def __init__(self, position: int, reason: str) -> None:
        self.position = position
        self.reason = reason
        super().__init__(
            error="non_utf8_payload",
            message="ongeldige UTF-8: de gedecodeerde bytes zijn geen geldige UTF-8 tekst en dus niet-tekstuele data.",
            detail=f"Fout op byte-positie {position}: {reason}. Gebruik een base64-string die UTF-8 tekst bevat.",
            status_code=422,
        )


__all__ = [
    "Base64ServiceError",
    "InputTooLargeError",
    "InvalidBase64CharacterError",
    "InvalidBase64LengthError",
    "Base64DecodeFailedError",
    "NonUtf8PayloadError",
]
