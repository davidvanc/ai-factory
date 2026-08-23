from __future__ import annotations
import os
from typing import List
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictStr

SERVICE_NAME: str = "base64_service"
SERVICE_VERSION: str = os.getenv("BASE64_SERVICE_VERSION", "1.0.0")
ALPHABETS: List[str] = ["standard", "url_safe"]
MAX_INPUT_BYTES: int = int(os.getenv("BASE64_MAX_INPUT_BYTES", "1048576"))
STANDARD_ALPHABET_CHARS: str = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
URLSAFE_ALPHABET_CHARS: str = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"


class EncodeRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    text: StrictStr = Field(..., description="Tekst die naar base64 wordt geëncodeerd.")
    url_safe: StrictBool = Field(default=False, description="Gebruik het URL-veilige alfabet ('-' en '_' in plaats van '+' en '/').")
    strip_padding: StrictBool = Field(default=False, description="Laat '=' padding weg in de output.")


class EncodeResponse(BaseModel):
    encoded: str = Field(..., description="De base64-representatie van de UTF-8 bytes van 'text'.")
    input_length: int = Field(..., ge=0, description="Aantal Unicode-tekens in de meegegeven 'text' (len(text)).")
    output_length: int = Field(..., ge=0, description="Aantal tekens in 'encoded' (len(encoded), dus na eventueel strippen van padding).")
    url_safe: bool = Field(..., description="Het gebruikte alfabet; overgenomen uit de request.")
    padding_stripped: bool = Field(..., description="True als '=' padding daadwerkelijk uit de output is verwijderd, anders False.")


class DecodeRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    data: StrictStr = Field(..., description="Base64-string die naar tekst wordt gedecodeerd; ontbrekende '=' padding wordt automatisch aangevuld.")
    url_safe: StrictBool = Field(default=False, description="Interpreteer de invoer volgens het URL-veilige alfabet ('-' en '_').")


class DecodeResponse(BaseModel):
    decoded: str = Field(..., description="De gedecodeerde UTF-8 tekst.")
    input_length: int = Field(..., ge=0, description="Aantal tekens in de meegegeven 'data' zoals ontvangen, vóór het aanvullen van padding (len(data)).")
    output_length: int = Field(..., ge=0, description="Aantal Unicode-tekens in 'decoded' (len(decoded)).")
    url_safe: bool = Field(..., description="Het gebruikte alfabet; overgenomen uit de request.")
    padding_added: int = Field(..., ge=0, le=2, description="Aantal '=' tekens dat automatisch is toegevoegd om de lengte deelbaar door 4 te maken (0, 1 of 2).")


class StatusResponse(BaseModel):
    status: str = Field(default="ok", description="Vaste waarde 'ok' zolang de service reageert.")
    service: str = Field(default=SERVICE_NAME, description="Servicenaam.")
    version: str = Field(default=SERVICE_VERSION, description="Serviceversie.")
    alphabets: List[str] = Field(default_factory=lambda: list(ALPHABETS), description="Ondersteunde base64-alfabetten.")
    max_input_bytes: int = Field(default=MAX_INPUT_BYTES, ge=1, description="Maximale invoergrootte in bytes.")


__all__ = [
    "SERVICE_NAME",
    "SERVICE_VERSION",
    "ALPHABETS",
    "MAX_INPUT_BYTES",
    "STANDARD_ALPHABET_CHARS",
    "URLSAFE_ALPHABET_CHARS",
    "EncodeRequest",
    "EncodeResponse",
    "DecodeRequest",
    "DecodeResponse",
    "StatusResponse",
]
