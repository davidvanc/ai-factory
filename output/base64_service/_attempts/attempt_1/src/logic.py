from __future__ import annotations
import base64
import binascii
from typing import Tuple
from src.errors import (
    Base64DecodeFailedError,
    InputTooLargeError,
    InvalidBase64CharacterError,
    InvalidBase64LengthError,
    NonUtf8PayloadError,
)
from src.models import MAX_INPUT_BYTES, STANDARD_ALPHABET_CHARS, URLSAFE_ALPHABET_CHARS


def check_input_size(size: int, limit: int = MAX_INPUT_BYTES) -> None:
    if size > limit:
        raise InputTooLargeError(size, limit)


def validate_base64_characters(data: str, url_safe: bool) -> None:
    alphabet = URLSAFE_ALPHABET_CHARS if url_safe else STANDARD_ALPHABET_CHARS
    allowed = set(alphabet) | {"="}
    for index, character in enumerate(data):
        if character not in allowed:
            raise InvalidBase64CharacterError(character, index, url_safe)


def compute_padding(data: str) -> int:
    length = len(data)
    if length % 4 == 1:
        raise InvalidBase64LengthError(length)
    return (-length) % 4


def encode_text(text: str, url_safe: bool = False, strip_padding: bool = False, limit: int = MAX_INPUT_BYTES) -> Tuple[str, bool]:
    raw = text.encode("utf-8")
    check_input_size(len(raw), limit)
    if url_safe:
        encoded = base64.urlsafe_b64encode(raw).decode("ascii")
    else:
        encoded = base64.b64encode(raw).decode("ascii")
    padding_stripped = False
    if strip_padding:
        stripped = encoded.rstrip("=")
        padding_stripped = stripped != encoded
        encoded = stripped
    return encoded, padding_stripped


def decode_data(data: str, url_safe: bool = False, limit: int = MAX_INPUT_BYTES) -> Tuple[str, int]:
    check_input_size(len(data.encode("utf-8")), limit)
    validate_base64_characters(data, url_safe)
    padding_added = compute_padding(data)
    padded = data + "=" * padding_added
    if url_safe:
        normalized = padded.replace("-", "+").replace("_", "/")
    else:
        normalized = padded
    try:
        raw = base64.b64decode(normalized, validate=True)
    except binascii.Error as exc:
        raise Base64DecodeFailedError(str(exc)) from exc
    try:
        decoded = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise NonUtf8PayloadError(exc.start, exc.reason) from exc
    return decoded, padding_added


__all__ = [
    "check_input_size",
    "validate_base64_characters",
    "compute_padding",
    "encode_text",
    "decode_data",
]
