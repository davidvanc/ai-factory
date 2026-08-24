from typing import Dict, Tuple

EMPTY_INPUT: str = "EMPTY_INPUT"
NOT_A_STRING: str = "NOT_A_STRING"
INVALID_CHARACTERS: str = "INVALID_CHARACTERS"
STRUCTURE_INVALID: str = "STRUCTURE_INVALID"
COUNTRY_NOT_SUPPORTED: str = "COUNTRY_NOT_SUPPORTED"
LENGTH_MISMATCH: str = "LENGTH_MISMATCH"
BBAN_FORMAT_INVALID: str = "BBAN_FORMAT_INVALID"
CHECKSUM_FAILED: str = "CHECKSUM_FAILED"

ALL_ERROR_CODES: Tuple[str, ...] = (
    EMPTY_INPUT,
    NOT_A_STRING,
    INVALID_CHARACTERS,
    STRUCTURE_INVALID,
    COUNTRY_NOT_SUPPORTED,
    LENGTH_MISMATCH,
    BBAN_FORMAT_INVALID,
    CHECKSUM_FAILED,
)

def make_error(code: str, message: str) -> Dict[str, str]:
    if code not in ALL_ERROR_CODES:
        raise ValueError(f"onbekende foutcode: {code}")
    return {"code": code, "message": message}
