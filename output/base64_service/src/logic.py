import base64
import binascii
import os
import string
from src.errors import (
    Base64Error,
    EMPTY_INPUT,
    INVALID_BASE64_CHARACTER,
    INVALID_PADDING,
    NOT_UTF8_DECODABLE,
)

BASE64_CORE_CHARS: str = string.ascii_uppercase + string.ascii_lowercase + string.digits
STANDARD_EXTRA_CHARS: str = "+/"
URLSAFE_EXTRA_CHARS: str = "-_"
STANDARD_CHARS: frozenset[str] = frozenset(BASE64_CORE_CHARS + STANDARD_EXTRA_CHARS)
URLSAFE_CHARS: frozenset[str] = frozenset(BASE64_CORE_CHARS + URLSAFE_EXTRA_CHARS)
SUPPORTED_ALPHABETS: list[str] = ["standard", "url_safe"]
SERVICE_NAME: str = os.getenv("SERVICE_NAME", "base64_service")
SERVICE_VERSION: str = os.getenv("SERVICE_VERSION", "1.0.0")


def encode_text(
    text: str, url_safe: bool = False, strip_padding: bool = False
) -> dict[str, object]:
    if text == "":
        raise Base64Error(
            EMPTY_INPUT,
            "Lege invoer: het veld 'text' mag geen lege string zijn",
            "Geef minimaal een teken mee in 'text' om te encoderen.",
        )
    raw = text.encode("utf-8")
    if url_safe:
        encoded = base64.urlsafe_b64encode(raw).decode("ascii")
    else:
        encoded = base64.b64encode(raw).decode("ascii")
    if strip_padding:
        encoded = encoded.rstrip("=")
    alphabet = "url_safe" if url_safe else "standard"
    return {
        "input_text": text,
        "encoded": encoded,
        "alphabet": alphabet,
        "input_bytes": len(raw),
        "output_length": len(encoded),
    }


def detect_alphabet(data: str, url_safe: bool = False) -> str:
    if url_safe:
        return "url_safe"
    if "-" in data or "_" in data:
        return "url_safe"
    return "standard"


def validate_characters(data: str, alphabet: str) -> None:
    allowed = URLSAFE_CHARS if alphabet == "url_safe" else STANDARD_CHARS
    extra = URLSAFE_EXTRA_CHARS if alphabet == "url_safe" else STANDARD_EXTRA_CHARS
    for index, char in enumerate(data):
        if char == "=":
            continue
        if char not in allowed:
            raise Base64Error(
                INVALID_BASE64_CHARACTER,
                f"Ongeldig teken '{char}' op positie {index} voor base64 alfabet",
                f"Het {alphabet} base64 alfabet staat alleen A-Z, a-z, 0-9, '{extra[0]}', '{extra[1]}' en '=' als padding toe.",
            )


def normalize_padding(data: str, fix_padding: bool) -> tuple[str, bool]:
    core = data.rstrip("=")
    pad_count = len(data) - len(core)
    if "=" in core:
        pos = core.index("=")
        raise Base64Error(
            INVALID_PADDING,
            f"Padding teken '=' op positie {pos} mag alleen aan het einde van de base64 string staan",
            "Base64 padding met '=' is uitsluitend toegestaan als afsluiting van de string.",
        )
    if pad_count > 2:
        raise Base64Error(
            INVALID_PADDING,
            f"Te veel padding tekens: {pad_count} '=' tekens gevonden, maximaal 2 toegestaan",
            "Een geldige base64 string eindigt met maximaal twee '=' tekens.",
        )
    remainder = len(core) % 4
    if remainder == 0:
        required_pad = 0
    elif remainder == 2:
        required_pad = 2
    elif remainder == 3:
        required_pad = 1
    else:
        raise Base64Error(
            INVALID_PADDING,
            f"Ongeldige base64 lengte: {len(core)} tekens zonder padding geeft een rest van 1 op, dat kan geen geldige base64 zijn",
            "Base64 data zonder padding heeft een lengte met rest 0, 2 of 3 modulo 4; deze fout is niet met fix_padding te herstellen.",
        )
    if pad_count == required_pad:
        return (data, False)
    if fix_padding:
        return (core + "=" * required_pad, True)
    raise Base64Error(
        INVALID_PADDING,
        f"Ongeldige padding: string heeft {pad_count} '=' teken(s) maar {required_pad} verwacht; gebruik fix_padding=true om dit automatisch te herstellen",
        "De lengte van de base64 data moet na padding een veelvoud van 4 zijn.",
    )


def decode_data(
    data: str, url_safe: bool = False, fix_padding: bool = True
) -> dict[str, object]:
    if data == "":
        raise Base64Error(
            EMPTY_INPUT,
            "Lege invoer: het veld 'data' mag geen lege string zijn",
            "Geef een niet-lege base64 string mee in 'data'.",
        )
    alphabet = detect_alphabet(data, url_safe)
    validate_characters(data, alphabet)
    normalized, padding_fixed = normalize_padding(data, fix_padding)
    try:
        if alphabet == "url_safe":
            raw = base64.urlsafe_b64decode(normalized)
        else:
            raw = base64.b64decode(normalized)
    except binascii.Error as exc:
        raise Base64Error(
            INVALID_PADDING,
            f"Base64 decodering mislukt: {exc}",
            "De base64 string kon ondanks geldige tekens en padding niet gedecodeerd worden.",
        )
    try:
        decoded = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise Base64Error(
            NOT_UTF8_DECODABLE,
            f"Gedecodeerde bytes zijn geen geldige UTF-8: {exc.reason} op byte positie {exc.start}",
            f"De base64 string levert {len(raw)} bytes op die niet als UTF-8 tekst gelezen kunnen worden.",
        )
    return {
        "input_data": data,
        "decoded": decoded,
        "alphabet": alphabet,
        "padding_fixed": padding_fixed,
        "output_length": len(decoded),
    }


def validate_data(data: str) -> dict[str, object]:
    try:
        if data == "":
            raise Base64Error(
                EMPTY_INPUT,
                "Lege invoer: het veld 'data' mag geen lege string zijn",
                "Geef een niet-lege base64 string mee in 'data'.",
            )
        alphabet = detect_alphabet(data, False)
        validate_characters(data, alphabet)
        normalize_padding(data, False)
        return {"data": data, "valid": True, "reason": None, "error_code": None}
    except Base64Error as exc:
        return {
            "data": data,
            "valid": False,
            "reason": exc.message,
            "error_code": exc.error_code,
        }


def service_status() -> dict[str, object]:
    return {
        "status": "ok",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "supported_alphabets": list(SUPPORTED_ALPHABETS),
    }
