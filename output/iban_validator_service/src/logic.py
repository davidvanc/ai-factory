import os
import re
from typing import Any, Dict, List
from src.errors import (
    BBAN_FORMAT_INVALID,
    CHECKSUM_FAILED,
    COUNTRY_NOT_SUPPORTED,
    EMPTY_INPUT,
    INVALID_CHARACTERS,
    LENGTH_MISMATCH,
    NOT_A_STRING,
    STRUCTURE_INVALID,
    make_error,
)
from src.iban_registry import IBAN_REGISTRY

SERVICE_VERSION: str = os.getenv("SERVICE_VERSION", "1.0.0")
MAX_BULK_ITEMS: int = int(os.getenv("MAX_BULK_ITEMS", "1000"))
STANDARDS: List[str] = ["ISO 13616", "ISO 7064 MOD 97-10"]
ALLOWED_CHARS_RE = re.compile(r"^[A-Z0-9]+$")


def normalize_iban(value: str) -> str:
    return "".join(value.split()).upper()


def format_print(compact: str) -> str:
    return " ".join(compact[i : i + 4] for i in range(0, len(compact), 4))


def iban_to_numeric(iban: str) -> str:
    compact = normalize_iban(iban)
    rearranged = compact[4:] + compact[:4]
    result = []
    for ch in rearranged:
        if ch.isdigit():
            result.append(ch)
        elif "A" <= ch <= "Z":
            result.append(str(ord(ch) - 55))
        else:
            raise ValueError(f"teken '{ch}' is niet toegestaan in een IBAN")
    return "".join(result)


def compute_mod97(iban: str) -> int:
    numeric = iban_to_numeric(iban)
    remainder = 0
    for ch in numeric:
        remainder = (remainder * 10 + int(ch)) % 97
    return remainder


def calculate_check_digits(country_code: str, bban: str) -> str:
    cc = normalize_iban(country_code)
    b = normalize_iban(bban)
    if len(cc) != 2 or not cc.isalpha():
        raise ValueError(f"ongeldige landcode: {country_code}")
    if b == "":
        raise ValueError("bban mag niet leeg zijn")
    remainder = compute_mod97(cc + "00" + b)
    return f"{98 - remainder:02d}"


def empty_checks() -> Dict[str, bool]:
    return {
        "structure": False,
        "country_supported": False,
        "length": False,
        "bban_format": False,
        "mod97": False,
    }


def validate_iban(value: Any) -> Dict[str, Any]:
    if not isinstance(value, str):
        return {
            "input": None,
            "valid": False,
            "iban": None,
            "formatted": None,
            "country_code": None,
            "country_name": None,
            "check_digits": None,
            "bban": None,
            "length": None,
            "expected_length": None,
            "bank_code": None,
            "account_number": None,
            "checks": empty_checks(),
            "errors": [
                make_error(
                    NOT_A_STRING, "waarde is geen string en kan niet als IBAN worden gelezen"
                )
            ],
        }

    compact = normalize_iban(value)
    if compact == "":
        return {
            "input": value,
            "valid": False,
            "iban": None,
            "formatted": None,
            "country_code": None,
            "country_name": None,
            "check_digits": None,
            "bban": None,
            "length": None,
            "expected_length": None,
            "bank_code": None,
            "account_number": None,
            "checks": empty_checks(),
            "errors": [make_error(EMPTY_INPUT, "lege waarde is geen geldig IBAN")],
        }

    if ALLOWED_CHARS_RE.match(compact) is None:
        bad = ", ".join(
            sorted({ch for ch in compact if not (ch.isdigit() or ("A" <= ch <= "Z"))})
        )
        return {
            "input": value,
            "valid": False,
            "iban": compact,
            "formatted": format_print(compact),
            "country_code": None,
            "country_name": None,
            "check_digits": None,
            "bban": None,
            "length": len(compact),
            "expected_length": None,
            "bank_code": None,
            "account_number": None,
            "checks": empty_checks(),
            "errors": [
                make_error(INVALID_CHARACTERS, f"IBAN bevat niet-toegestane tekens: {bad}")
            ],
        }

    if len(compact) < 5 or not compact[:2].isalpha() or not compact[2:4].isdigit():
        return {
            "input": value,
            "valid": False,
            "iban": compact,
            "formatted": format_print(compact),
            "country_code": None,
            "country_name": None,
            "check_digits": None,
            "bban": None,
            "length": len(compact),
            "expected_length": None,
            "bank_code": None,
            "account_number": None,
            "checks": empty_checks(),
            "errors": [
                make_error(
                    STRUCTURE_INVALID,
                    "IBAN moet minimaal 5 tekens lang zijn en beginnen met 2 letters landcode gevolgd door 2 controlecijfers",
                )
            ],
        }

    checks = empty_checks()
    checks["structure"] = True
    country_code = compact[:2]
    check_digits = compact[2:4]
    bban = compact[4:]
    length = len(compact)
    iban = compact
    formatted = format_print(compact)

    entry = IBAN_REGISTRY.get(country_code)
    if entry is None:
        return {
            "input": value,
            "valid": False,
            "iban": iban,
            "formatted": formatted,
            "country_code": country_code,
            "country_name": None,
            "check_digits": check_digits,
            "bban": bban,
            "length": length,
            "expected_length": None,
            "bank_code": None,
            "account_number": None,
            "checks": checks,
            "errors": [
                make_error(
                    COUNTRY_NOT_SUPPORTED,
                    f"landcode '{country_code}' staat niet in de IBAN-registry",
                )
            ],
        }

    checks["country_supported"] = True
    country_name = entry["country_name"]
    expected_length = entry["iban_length"]
    if length != expected_length:
        return {
            "input": value,
            "valid": False,
            "iban": iban,
            "formatted": formatted,
            "country_code": country_code,
            "country_name": country_name,
            "check_digits": check_digits,
            "bban": bban,
            "length": length,
            "expected_length": expected_length,
            "bank_code": None,
            "account_number": None,
            "checks": checks,
            "errors": [
                make_error(
                    LENGTH_MISMATCH,
                    f"IBAN-lengte {length} wijkt af van de verwachte lengte {expected_length} voor {country_code}",
                )
            ],
        }

    checks["length"] = True
    start, stop = entry["bank_code_slice"]
    bank_code = compact[start:stop]
    account_number = compact[stop:]
    if re.match(entry["bban_pattern"], bban) is None:
        return {
            "input": value,
            "valid": False,
            "iban": iban,
            "formatted": formatted,
            "country_code": country_code,
            "country_name": country_name,
            "check_digits": check_digits,
            "bban": bban,
            "length": length,
            "expected_length": expected_length,
            "bank_code": bank_code,
            "account_number": account_number,
            "checks": checks,
            "errors": [
                make_error(
                    BBAN_FORMAT_INVALID,
                    f"BBAN '{bban}' past niet op het patroon {entry['bban_pattern']} voor {country_code}",
                )
            ],
        }

    checks["bban_format"] = True
    try:
        remainder = compute_mod97(compact)
    except ValueError:
        remainder = 99
    if remainder != 1:
        return {
            "input": value,
            "valid": False,
            "iban": iban,
            "formatted": formatted,
            "country_code": country_code,
            "country_name": country_name,
            "check_digits": check_digits,
            "bban": bban,
            "length": length,
            "expected_length": expected_length,
            "bank_code": bank_code,
            "account_number": account_number,
            "checks": checks,
            "errors": [
                make_error(
                    CHECKSUM_FAILED, f"mod-97 checksum is {remainder}, verwacht 1"
                )
            ],
        }

    checks["mod97"] = True
    return {
        "input": value,
        "valid": True,
        "iban": iban,
        "formatted": formatted,
        "country_code": country_code,
        "country_name": country_name,
        "check_digits": check_digits,
        "bban": bban,
        "length": length,
        "expected_length": expected_length,
        "bank_code": bank_code,
        "account_number": account_number,
        "checks": checks,
        "errors": [],
    }
