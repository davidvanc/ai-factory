from __future__ import annotations
import os
from typing import Dict, List

SERVICE_NAME: str = os.getenv("SERVICE_NAME", "base64_codec_service")
SERVICE_VERSION: str = os.getenv("SERVICE_VERSION", "1.0.0")
MAX_INPUT_BYTES: int = int(os.getenv("MAX_INPUT_BYTES", "1048576"))
MAX_BODY_BYTES: int = MAX_INPUT_BYTES * 4 + 1024
DEFAULT_ENCODING: str = os.getenv("DEFAULT_ENCODING", "utf-8")
SUPPORTED_ALPHABETS: List[str] = ["standard", "url_safe"]
ENCODING_ALIASES: Dict[str, str] = {
    "utf-8": "utf-8", "utf8": "utf-8", "utf_8": "utf-8",
    "ascii": "ascii", "us-ascii": "ascii",
    "latin-1": "latin-1", "latin1": "latin-1", "iso-8859-1": "latin-1",
    "utf-16": "utf-16", "utf16": "utf-16",
    "utf-32": "utf-32", "utf32": "utf-32",
    "cp1252": "cp1252", "windows-1252": "cp1252",
}
SUPPORTED_ENCODINGS: List[str] = ["utf-8", "ascii", "latin-1", "utf-16", "utf-32", "cp1252"]
