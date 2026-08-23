from __future__ import annotations
import base64
import binascii
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from src import config
from src import errors
from src.errors import ApiError
from src.models import DecodeResponse, EncodeResponse, ValidateResponse

WHITESPACE: str = " \t\n\r\x0b\f"
ALNUM: str = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
STANDARD_EXTRA: str = "+/"
URLSAFE_EXTRA: str = "-_"

_COUNTERS: Dict[str, int] = {"encode": 0, "decode": 0, "validate": 0}
_TOTAL: int = 0

def reset_state() -> None:
    global _TOTAL
    _COUNTERS.clear()
    _COUNTERS.update({"encode": 0, "decode": 0, "validate": 0})
    _TOTAL = 0

def _increment(name: str) -> None:
    global _TOTAL
    _COUNTERS[name] = _COUNTERS.get(name, 0) + 1
    _TOTAL = _TOTAL + 1

def get_counters() -> Dict[str, int]:
    return {
        "encode": _COUNTERS.get("encode", 0),
        "decode": _COUNTERS.get("decode", 0),
        "validate": _COUNTERS.get("validate", 0),
        "total": _TOTAL
    }

def normalize_encoding(encoding: str) -> str:
    key = encoding.strip().lower()
    if key in config.ENCODING_ALIASES:
        return config.ENCODING_ALIASES[key]
    key2 = key.replace("_", "-")
    if key2 in config.ENCODING_ALIASES:
        return config.ENCODING_ALIASES[key2]
    raise errors.unsupported_encoding(encoding, config.SUPPORTED_ENCODINGS)

def strip_whitespace(data: str) -> Tuple[str, List[int]]:
    cleaned = []
    index_map = []
    for i, c in enumerate(data):
        if c in WHITESPACE:
            continue
        cleaned.append(c)
        index_map.append(i)
    return "".join(cleaned), index_map

@dataclass(frozen=True)
class Base64Check:
    valid: bool
    cleaned: str
    alphabet: str
    error_code: Optional[str]
    message: Optional[str]
    position: Optional[int]

def check_base64(data: str) -> Base64Check:
    cleaned, index_map = strip_whitespace(data)
    if cleaned == "":
        return Base64Check(False, "", "standard", errors.EMPTY_INPUT, "De invoer is leeg of bevat alleen whitespace.", None)
    std_positions = [i for i, c in enumerate(cleaned) if c in STANDARD_EXTRA]
    url_positions = [i for i, c in enumerate(cleaned) if c in URLSAFE_EXTRA]
    if std_positions and url_positions:
        p = index_map[max(std_positions[0], url_positions[0])]
        return Base64Check(False, cleaned, "mixed", errors.MIXED_ALPHABET, f"Invoer mengt het standaard-alfabet ('+/') met het URL-veilige alfabet ('-_') op positie {p}.", p)
    alphabet = "url_safe" if url_positions else "standard"
    allowed = ALNUM + (URLSAFE_EXTRA if alphabet == "url_safe" else STANDARD_EXTRA)
    for i, c in enumerate(cleaned):
        if c == "=":
            continue
        if c not in allowed:
            p = index_map[i]
            return Base64Check(False, cleaned, alphabet, errors.INVALID_BASE64_CHARACTER, f"Ongeldig base64-teken '{c}' op positie {p}.", p)
    if "=" in cleaned:
        first_eq = cleaned.index("=")
        for j in range(first_eq + 1, len(cleaned)):
            if cleaned[j] != "=":
                p = index_map[j]
                return Base64Check(False, cleaned, alphabet, errors.INVALID_PADDING, f"Padding-teken '=' mag alleen aan het einde staan; teken '{cleaned[j]}' staat na de padding op positie {p}.", p)
    pad_count = cleaned.count("=")
    if pad_count > 2:
        third_eq = [i for i, c in enumerate(cleaned) if c == "="][2]
        p = index_map[third_eq]
        return Base64Check(False, cleaned, alphabet, errors.INVALID_PADDING, f"Te veel padding-tekens ('='): maximaal 2 toegestaan, gevonden {pad_count}.", p)
    if len(cleaned) % 4 != 0:
        return Base64Check(False, cleaned, alphabet, errors.INVALID_PADDING, f"Lengte van de base64-invoer is {len(cleaned)}, wat niet deelbaar door 4 is; padding met '=' ontbreekt.", None)
    try:
        base64.b64decode(cleaned, altchars=b"-_" if alphabet == "url_safe" else None, validate=True)
    except binascii.Error as exc:
        return Base64Check(False, cleaned, alphabet, errors.DECODE_FAILED, f"Kon de base64-invoer niet decoderen: {exc}.", None)
    return Base64Check(True, cleaned, alphabet, None, None, None)

def decode_bytes(cleaned: str, alphabet: str) -> bytes:
    return base64.b64decode(cleaned, altchars=b"-_" if alphabet == "url_safe" else None, validate=True)

def encode_text(text: str, url_safe: bool = False, encoding: str = config.DEFAULT_ENCODING) -> EncodeResponse:
    _increment("encode")
    enc = normalize_encoding(encoding)
    if text == "":
        raise errors.empty_input("text")
    try:
        raw = text.encode(enc)
    except UnicodeEncodeError as exc:
        raise ApiError(422, errors.NOT_ENCODABLE_TEXT, f"Tekst kan niet met '{enc}' worden gecodeerd: {exc.reason} op positie {exc.start}.", detail=f"Gebruik encoding 'utf-8' of verwijder het teken op positie {exc.start}.", position=exc.start)
    if len(raw) > config.MAX_INPUT_BYTES:
        raise errors.input_too_large(len(raw), config.MAX_INPUT_BYTES)
    encoded_bytes = base64.urlsafe_b64encode(raw) if url_safe else base64.b64encode(raw)
    encoded = encoded_bytes.decode("ascii")
    return EncodeResponse(encoded=encoded, input_bytes=len(raw), output_length=len(encoded), url_safe=url_safe, encoding=enc)

def decode_base64_to_text(data: str, encoding: str = config.DEFAULT_ENCODING, strict: bool = True) -> DecodeResponse:
    _increment("decode")
    enc = normalize_encoding(encoding)
    if len(data) > config.MAX_INPUT_BYTES:
        raise errors.input_too_large(len(data), config.MAX_INPUT_BYTES)
    check = check_base64(data)
    if not check.valid and check.error_code == errors.EMPTY_INPUT:
        raise errors.empty_input("data")
    if not check.valid:
        raise ApiError(400, check.error_code, check.message, detail=f"Alfabet: {check.alphabet}. Genormaliseerde lengte: {len(check.cleaned)}.", position=check.position)
    raw = decode_bytes(check.cleaned, check.alphabet)
    if strict:
        try:
            text = raw.decode(enc)
        except UnicodeDecodeError as exc:
            raise ApiError(400, errors.NOT_DECODABLE_TEXT, f"De gedecodeerde bytes zijn geen geldige {enc}-tekst: {exc.reason} op byte-positie {exc.start}.", detail=f"Zet strict=false om ongeldige bytes te vervangen door U+FFFD.", position=exc.start)
    else:
        text = raw.decode(enc, errors="replace")
    return DecodeResponse(decoded=text, input_length=len(check.cleaned), output_bytes=len(raw), encoding=enc, detected_alphabet=check.alphabet)

def validate_base64_string(data: str) -> ValidateResponse:
    _increment("validate")
    if len(data) > config.MAX_INPUT_BYTES:
        return ValidateResponse(valid=False, error_code=errors.INPUT_TOO_LARGE, message=f"Invoer is {len(data)} tekens; maximaal {config.MAX_INPUT_BYTES} toegestaan.", position=None)
    check = check_base64(data)
    if check.valid:
        return ValidateResponse(valid=True, error_code=None, message=None, position=None)
    else:
        return ValidateResponse(valid=False, error_code=check.error_code, message=check.message, position=check.position)
