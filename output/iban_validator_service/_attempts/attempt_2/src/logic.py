import re
from typing import Any, Dict, List, Optional, Tuple
from src import errors
from src.country_registry import get_country

ALNUM_RE = re.compile(r"^[A-Z0-9]+$")
STRUCTURE_RE = re.compile(r"^[A-Z]{2}[0-9]{2}[A-Z0-9]+$")
COUNTRY_RE = re.compile(r"^[A-Z]{2}$")
DIGITS2_RE = re.compile(r"^[0-9]{2}$")
FORBIDDEN_CHECK_DIGITS = frozenset({"00", "01", "99"})

def normalize_iban(raw: str) -> str:
    return "".join(str(raw).split()).upper()

def format_print(compact: str) -> str:
    if not compact:
        return ""
    return " ".join(compact[i:i+4] for i in range(0, len(compact), 4))

def format_iban(compact: str, style: str = "print") -> str:
    if style == "print":
        return format_print(compact)
    if style in ("compact", "electronic"):
        return compact
    raise ValueError(f"onbekende style: {style}")

def mod97(compact: str) -> int:
    if not compact:
        raise ValueError("lege IBAN voor mod-97 berekening")
    rearranged = compact[4:] + compact[:4]
    digits = []
    for ch in rearranged:
        if "0" <= ch <= "9":
            digits.append(ch)
        elif "A" <= ch <= "Z":
            digits.append(str(ord(ch) - 55))
        else:
            raise ValueError(f"ongeldig teken voor mod-97 berekening: {ch}")
    return int("".join(digits)) % 97

def compute_mod97(iban: str) -> int:
    compact = normalize_iban(iban)
    return mod97(compact)

def extract_parts(compact: str, entry: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    bban = compact[4:]
    bank_len = entry["bank_length"]
    branch_len = entry["branch_length"]
    bank_identifier = bban[0:bank_len] or None
    branch_identifier = None
    if branch_len > 0:
        branch_part = bban[bank_len:bank_len+branch_len]
        branch_identifier = branch_part or None
    account_start = bank_len + branch_len
    account_number = bban[account_start:] or None
    return bank_identifier, branch_identifier, account_number

def validate_iban(raw: str) -> Dict[str, Any]:
    input_val = raw
    compact = normalize_iban(raw)
    length = len(compact)
    formatted = format_print(compact)
    errors_list = []
    country_code = None
    check_digits = None
    bban = None
    expected_length = None
    checksum_mod97 = None
    bank_identifier = None
    branch_identifier = None
    account_number = None
    valid = False

    if compact == "":
        errors_list.append(errors.make_error(errors.EMPTY_INPUT))
        return {
            "input": input_val,
            "valid": False,
            "country_code": country_code,
            "check_digits": check_digits,
            "bban": bban,
            "length": length,
            "expected_length": expected_length,
            "checksum_mod97": checksum_mod97,
            "formatted": formatted,
            "compact": compact,
            "bank_identifier": bank_identifier,
            "branch_identifier": branch_identifier,
            "account_number": account_number,
            "errors": errors_list,
        }

    if COUNTRY_RE.match(compact[:2]):
        country_code = compact[:2]
    if DIGITS2_RE.match(compact[2:4]):
        check_digits = compact[2:4]
    entry = None
    if country_code is not None:
        entry = get_country(country_code)
        if entry is not None:
            expected_length = entry["iban_length"]

    if not ALNUM_RE.match(compact):
        errors_list.append(errors.make_error(errors.INVALID_CHARACTERS))
        return {
            "input": input_val,
            "valid": False,
            "country_code": country_code,
            "check_digits": check_digits,
            "bban": bban,
            "length": length,
            "expected_length": expected_length,
            "checksum_mod97": checksum_mod97,
            "formatted": formatted,
            "compact": compact,
            "bank_identifier": bank_identifier,
            "branch_identifier": branch_identifier,
            "account_number": account_number,
            "errors": errors_list,
        }

    if not STRUCTURE_RE.match(compact):
        errors_list.append(errors.make_error(errors.INVALID_STRUCTURE))
        return {
            "input": input_val,
            "valid": False,
            "country_code": country_code,
            "check_digits": check_digits,
            "bban": bban,
            "length": length,
            "expected_length": expected_length,
            "checksum_mod97": checksum_mod97,
            "formatted": formatted,
            "compact": compact,
            "bank_identifier": bank_identifier,
            "branch_identifier": branch_identifier,
            "account_number": account_number,
            "errors": errors_list,
        }

    bban = compact[4:]
    if entry is None:
        errors_list.append(errors.make_error(errors.UNKNOWN_COUNTRY, country_code=country_code))
        return {
            "input": input_val,
            "valid": False,
            "country_code": country_code,
            "check_digits": check_digits,
            "bban": bban,
            "length": length,
            "expected_length": expected_length,
            "checksum_mod97": checksum_mod97,
            "formatted": formatted,
            "compact": compact,
            "bank_identifier": bank_identifier,
            "branch_identifier": branch_identifier,
            "account_number": account_number,
            "errors": errors_list,
        }

    if length != entry["iban_length"]:
        errors_list.append(errors.make_error(errors.INVALID_LENGTH,
                                             length=length,
                                             expected_length=entry["iban_length"],
                                             country_code=country_code))
        expected_length = entry["iban_length"]
        return {
            "input": input_val,
            "valid": False,
            "country_code": country_code,
            "check_digits": check_digits,
            "bban": bban,
            "length": length,
            "expected_length": expected_length,
            "checksum_mod97": checksum_mod97,
            "formatted": formatted,
            "compact": compact,
            "bank_identifier": bank_identifier,
            "branch_identifier": branch_identifier,
            "account_number": account_number,
            "errors": errors_list,
        }

    bank_identifier, branch_identifier, account_number = extract_parts(compact, entry)

    if not re.fullmatch(entry["bban_regex"], bban):
        errors_list.append(errors.make_error(errors.INVALID_FORMAT,
                                             bban=bban,
                                             bban_pattern=entry["bban_pattern"],
                                             country_code=country_code))
        return {
            "input": input_val,
            "valid": False,
            "country_code": country_code,
            "check_digits": check_digits,
            "bban": bban,
            "length": length,
            "expected_length": expected_length,
            "checksum_mod97": checksum_mod97,
            "formatted": formatted,
            "compact": compact,
            "bank_identifier": bank_identifier,
            "branch_identifier": branch_identifier,
            "account_number": account_number,
            "errors": errors_list,
        }

    if check_digits in FORBIDDEN_CHECK_DIGITS:
        errors_list.append(errors.make_error(errors.INVALID_CHECK_DIGITS,
                                             check_digits=check_digits))
        return {
            "input": input_val,
            "valid": False,
            "country_code": country_code,
            "check_digits": check_digits,
            "bban": bban,
            "length": length,
            "expected_length": expected_length,
            "checksum_mod97": checksum_mod97,
            "formatted": formatted,
            "compact": compact,
            "bank_identifier": bank_identifier,
            "branch_identifier": branch_identifier,
            "account_number": account_number,
            "errors": errors_list,
        }

    try:
        checksum_mod97 = mod97(compact)
        if checksum_mod97 != 1:
            errors_list.append(errors.make_error(errors.CHECKSUM_FAILED))
            valid = False
        else:
            valid = True
    except Exception as exc:
        errors_list.append(errors.make_error(errors.INTERNAL_ERROR, detail=str(exc)))
        valid = False

    return {
        "input": input_val,
        "valid": valid,
        "country_code": country_code,
        "check_digits": check_digits,
        "bban": bban,
        "length": length,
        "expected_length": expected_length,
        "checksum_mod97": checksum_mod97,
        "formatted": formatted,
        "compact": compact,
        "bank_identifier": bank_identifier,
        "branch_identifier": branch_identifier,
        "account_number": account_number,
        "errors": errors_list,
    }

def validate_bulk_item(index: int, item: Any, style: str = "print") -> Dict[str, Any]:
    try:
        if not isinstance(item, str):
            return {
                "index": index,
                "input": item,
                "status": "error",
                "valid": False,
                "country_code": None,
                "formatted": None,
                "compact": None,
                "length": None,
                "expected_length": None,
                "errors": [errors.make_error(errors.NOT_A_STRING)],
            }
        res = validate_iban(item)
        status = "valid" if res["valid"] else "invalid"
        formatted = format_iban(res["compact"], style)
        return {
            "index": index,
            "input": item,
            "status": status,
            "valid": res["valid"],
            "country_code": res["country_code"],
            "formatted": formatted,
            "compact": res["compact"],
            "length": res["length"],
            "expected_length": res["expected_length"],
            "errors": res["errors"],
        }
    except Exception as exc:
        return {
            "index": index,
            "input": item,
            "status": "error",
            "valid": False,
            "country_code": None,
            "formatted": None,
            "compact": None,
            "length": None,
            "expected_length": None,
            "errors": [errors.make_error(errors.INTERNAL_ERROR, detail=str(exc))],
        }

def validate_bulk(items: List[Any], style: str = "print", fail_fast: bool = False) -> Dict[str, Any]:
    results = []
    valid_count = 0
    invalid_count = 0
    error_count = 0
    stopped_early = False

    for index, item in enumerate(items):
        result = validate_bulk_item(index, item, style)
        results.append(result)
        if result["status"] == "valid":
            valid_count += 1
        elif result["status"] == "invalid":
            invalid_count += 1
        else:
            error_count += 1

        if fail_fast and result["status"] != "valid":
            stopped_early = True
            break

    return {
        "count": len(results),
        "summary": {
            "valid": valid_count,
            "invalid": invalid_count,
            "errors": error_count,
            "stopped_early": stopped_early,
        },
        "results": results,
    }
