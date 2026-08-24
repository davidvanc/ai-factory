import pytest
from src import country_registry
from src import errors
from src.logic import (
    compute_mod97,
    extract_parts,
    format_iban,
    format_print,
    mod97,
    normalize_iban,
    validate_bulk,
    validate_bulk_item,
    validate_iban,
)


@pytest.fixture(autouse=True)
def _reset_registry():
    country_registry.reset_state()
    yield
    country_registry.reset_state()


def codes(result):
    return [e["code"] for e in result["errors"]]


def test_normalize_iban_removes_whitespace_and_uppercases():
    assert normalize_iban(" nl91 abna 0417 1643 00 ") == "NL91ABNA0417164300"
    assert normalize_iban("\tde89\n3704") == "DE893704"
    assert normalize_iban("   ") == ""


def test_format_print_groups_of_four():
    assert format_print("NL91ABNA0417164300") == "NL91 ABNA 0417 1643 00"
    assert format_print("XX00INVALID") == "XX00 INVA LID"
    assert format_print("") == ""


def test_format_iban_styles():
    compact = "NL91ABNA0417164300"
    assert format_iban(compact, "print") == "NL91 ABNA 0417 1643 00"
    assert format_iban(compact, "compact") == compact
    assert format_iban(compact, "electronic") == compact


def test_format_iban_unknown_style_raises_value_error():
    with pytest.raises(ValueError, match="onbekende style"):
        format_iban("NL91ABNA0417164300", "banana")


def test_mod97_reference_ibans_equal_one():
    assert mod97("GB82WEST12345698765432") == 1
    assert mod97("BE68539007547034") == 1
    assert mod97("NL91ABNA0417164300") == 1
    assert mod97("DE89370400440532013000") == 1


def test_mod97_wrong_checksum_not_one_and_invalid_chars_raise():
    assert mod97("NL91ABNA0417164301") != 1
    with pytest.raises(ValueError):
        mod97("NL91-ABNA0417164300")
    with pytest.raises(ValueError):
        mod97("")


def test_compute_mod97_normalizes_input():
    assert compute_mod97("nl91 abna 0417 1643 00") == 1
    assert compute_mod97("GB82WEST12345698765432") == 1
    assert compute_mod97("NL91ABNA0417164301") != 1
    with pytest.raises(ValueError):
        compute_mod97("   ")
    with pytest.raises(ValueError):
        compute_mod97("NL91-ABNA0417164300")


def test_validate_iban_valid_nl_all_fields():
    result = validate_iban("NL91 ABNA 0417 1643 00")
    assert result["valid"] is True
    assert result["errors"] == []
    assert result["input"] == "NL91 ABNA 0417 1643 00"
    assert result["compact"] == "NL91ABNA0417164300"
    assert result["formatted"] == "NL91 ABNA 0417 1643 00"
    assert result["country_code"] == "NL"
    assert result["check_digits"] == "91"
    assert result["bban"] == "ABNA0417164300"
    assert result["length"] == 18
    assert result["expected_length"] == 18
    assert result["checksum_mod97"] == 1
    assert result["bank_identifier"] == "ABNA"
    assert result["branch_identifier"] is None
    assert result["account_number"] == "0417164300"


def test_validate_iban_empty_input():
    result = validate_iban("   ")
    assert result["valid"] is False
    assert codes(result) == ["EMPTY_INPUT"]
    assert result["length"] == 0
    assert result["compact"] == ""
    assert result["formatted"] == ""
    assert result["country_code"] is None


def test_validate_iban_invalid_characters():
    result = validate_iban("NL91-ABNA*0417")
    assert codes(result) == ["INVALID_CHARACTERS"]
    assert result["valid"] is False
    assert result["country_code"] == "NL"
    assert result["bban"] is None
    assert result["checksum_mod97"] is None


def test_validate_iban_invalid_structure():
    result = validate_iban("1234ABCDEF")
    assert codes(result) == ["INVALID_STRUCTURE"]
    assert result["valid"] is False
    assert result["country_code"] is None
    result2 = validate_iban("NL9")
    assert codes(result2) == ["INVALID_STRUCTURE"]
    assert result2["valid"] is False


def test_validate_iban_unknown_country():
    result = validate_iban("XX00INVALID")
    assert codes(result) == ["UNKNOWN_COUNTRY"]
    assert result["country_code"] == "XX"
    assert result["expected_length"] is None
    assert result["formatted"] == "XX00 INVA LID"
    assert result["bban"] == "INVALID"
    assert result["errors"][0]["message"] == "Landcode 'XX' staat niet in de ISO 13616 registry"


def test_validate_iban_invalid_length():
    result = validate_iban("FR761234")
    assert codes(result) == ["INVALID_LENGTH"]
    assert result["length"] == 8
    assert result["expected_length"] == 27
    assert result["country_code"] == "FR"
    assert result["errors"][0]["message"] == "Lengte 8 wijkt af van verwachte lengte 27 voor land FR"


def test_validate_iban_invalid_format():
    result = validate_iban("NL911234041716430A")
    assert codes(result) == ["INVALID_FORMAT"]
    assert result["length"] == 18
    assert result["expected_length"] == 18
    assert result["checksum_mod97"] is None


def test_validate_iban_forbidden_check_digits():
    for cd in ("00", "01", "99"):
        result = validate_iban(f"NL{cd}ABNA0417164300")
        assert result["valid"] is False
        assert codes(result) == ["INVALID_CHECK_DIGITS"]


def test_validate_iban_checksum_failed():
    result = validate_iban("NL91ABNA0417164301")
    assert codes(result) == ["CHECKSUM_FAILED"]
    assert result["valid"] is False
    assert result["checksum_mod97"] != 1
    assert result["errors"][0]["message"] == "mod-97 checksum is niet gelijk aan 1"


def test_extract_parts_uses_registry_lengths():
    fr_entry = country_registry.get_country("FR")
    assert extract_parts("FR1420041010050500013M02606", fr_entry) == ("20041", "01005", "0500013M02606")
    de_entry = country_registry.get_country("DE")
    assert extract_parts("DE89370400440532013000", de_entry) == ("37040044", None, "0532013000")


def test_validate_bulk_item_non_string_and_exception_paths():
    result = validate_bulk_item(0, None, "print")
    assert result["status"] == "error"
    assert result["valid"] is False
    assert codes(result) == ["NOT_A_STRING"]
    assert result["compact"] is None
    assert result["length"] is None
    assert result["index"] == 0
    result2 = validate_bulk_item(3, "NL91ABNA0417164300", "compact")
    assert result2["status"] == "valid"
    assert result2["formatted"] == "NL91ABNA0417164300"
    assert result2["index"] == 3


def test_validate_bulk_counts_and_fail_fast():
    result = validate_bulk(["NL91ABNA0417164300", "XX00INVALID", "BE68539007547034"], "print", False)
    assert result["count"] == 3
    assert result["summary"] == {"valid": 2, "invalid": 1, "errors": 0, "stopped_early": False}
    result2 = validate_bulk(["XX00INVALID", "BE68539007547034"], "print", True)
    assert result2["count"] == 1
    assert result2["summary"]["stopped_early"] is True
    assert result2["summary"]["invalid"] == 1
    assert result2["summary"]["valid"] == 0
    result3 = validate_bulk([], "print", False)
    assert result3 == {"count": 0, "summary": {"valid": 0, "invalid": 0, "errors": 0, "stopped_early": False}, "results": []}


def test_no_hardcoded_country_lengths_new_registry_entry_works():
    result = validate_iban("QQ73123456")
    assert codes(result) == ["UNKNOWN_COUNTRY"]
    country_registry.REGISTRY["QQ"] = {
        "country_code": "QQ",
        "name": "Testland",
        "iban_length": 10,
        "bban_pattern": "6!n",
        "bban_regex": "^[0-9]{6}$",
        "sepa": False,
        "example": "QQ73123456",
        "bank_length": 3,
        "branch_length": 0,
    }
    check = 98 - mod97("QQ00" + "123456")
    iban = "QQ" + f"{check:02d}" + "123456"
    result2 = validate_iban(iban)
    assert result2["valid"] is True
    assert result2["errors"] == []
    assert result2["expected_length"] == 10
    assert result2["country_code"] == "QQ"
    assert result2["bank_identifier"] == "123"
    assert result2["branch_identifier"] is None
    assert result2["account_number"] == "456"
    result3 = validate_iban("QQ7312345")
    assert codes(result3) == ["INVALID_LENGTH"]
    assert result3["expected_length"] == 10


def test_make_error_formats_message_and_unknown_code_raises():
    assert errors.make_error(errors.CHECKSUM_FAILED) == {"code": "CHECKSUM_FAILED", "message": "mod-97 checksum is niet gelijk aan 1"}
    assert errors.make_error(errors.UNKNOWN_COUNTRY, country_code="ZZ")["message"] == "Landcode 'ZZ' staat niet in de ISO 13616 registry"
    with pytest.raises(KeyError):
        errors.make_error("NIET_BESTAANDE_CODE")
