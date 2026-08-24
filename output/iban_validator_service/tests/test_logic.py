import pytest
from src.errors import make_error
from src.iban_registry import IBAN_REGISTRY, get_country, reset_state
from src.logic import calculate_check_digits, compute_mod97, empty_checks, format_print, iban_to_numeric, normalize_iban, validate_iban


@pytest.fixture(autouse=True)
def _reset():
    reset_state()
    yield
    reset_state()


def test_normalize_iban_strips_whitespace_and_uppercases():
    assert normalize_iban(" nl91\tabna 0417\n1643 00 ") == "NL91ABNA0417164300"
    assert normalize_iban("   ") == ""


def test_iban_to_numeric_letter_mapping_and_rearrangement():
    assert iban_to_numeric("XY12") == "333412"
    assert iban_to_numeric("NL91ABNA0417164300") == "101123100417164300232191"
    with pytest.raises(ValueError):
        iban_to_numeric("NL91-ABNA")


def test_compute_mod97_valid_is_one_and_invalid_is_not():
    assert compute_mod97("NL91ABNA0417164300") == 1
    assert compute_mod97("DE89370400440532013000") == 1
    assert compute_mod97("NL91ABNA0417164301") != 1


def test_calculate_check_digits_known_values():
    assert calculate_check_digits("NL", "ABNA0417164300") == "91"
    assert calculate_check_digits("DE", "370400440532013000") == "89"
    assert calculate_check_digits("GB", "WEST12345698765432") == "82"
    assert calculate_check_digits("BE", "539007547034") == "68"
    assert len(calculate_check_digits("nl ", " abna0417164300")) == 2


def test_calculate_check_digits_rejects_bad_input():
    with pytest.raises(ValueError):
        calculate_check_digits("N1", "ABNA0417164300")
    with pytest.raises(ValueError):
        calculate_check_digits("NL", "")


def test_format_print_groups_of_four():
    assert format_print("NL91ABNA0417164300") == "NL91 ABNA 0417 1643 00"
    assert format_print("XX00INVALID") == "XX00 INVA LID"
    assert format_print("") == ""


def test_empty_checks_all_false():
    assert empty_checks() == {"structure": False, "country_supported": False, "length": False, "bban_format": False, "mod97": False}


def test_validate_iban_uses_registry_as_data_table():
    cd = calculate_check_digits("ZZ", "123456")
    IBAN_REGISTRY["ZZ"] = {"country_name": "Testland", "iban_length": 10, "bban_pattern": "^[0-9]{6}$", "bank_code_slice": [4, 7], "sepa": False, "example": "ZZ" + cd + "123456"}
    result = validate_iban("ZZ" + cd + "123456")
    assert result["valid"] is True
    assert result["country_code"] == "ZZ"
    assert result["country_name"] == "Testland"
    assert result["expected_length"] == 10
    assert result["length"] == 10
    assert result["bank_code"] == "123"
    assert result["account_number"] == "456"
    assert result["checks"] == {"structure": True, "country_supported": True, "length": True, "bban_format": True, "mod97": True}
    assert result["errors"] == []


def test_validate_iban_non_string_returns_not_a_string():
    result = validate_iban(None)
    assert result["valid"] is False
    assert result["input"] is None
    assert result["iban"] is None
    assert result["errors"][0]["code"] == "NOT_A_STRING"
    assert result["checks"]["structure"] is False
    assert validate_iban(42)["errors"][0]["code"] == "NOT_A_STRING"


def test_validate_iban_empty_input():
    result = validate_iban("   ")
    assert result["valid"] is False
    assert result["iban"] is None
    assert result["formatted"] is None
    assert result["country_code"] is None
    assert result["errors"][0]["code"] == "EMPTY_INPUT"
    assert all(v is False for v in result["checks"].values())


def test_validate_iban_invalid_characters():
    result = validate_iban("NL91-ABNA-0417")
    assert result["valid"] is False
    assert result["errors"][0]["code"] == "INVALID_CHARACTERS"
    assert "-" in result["errors"][0]["message"]
    assert result["checks"]["structure"] is False


def test_validate_iban_structure_invalid():
    assert validate_iban("N1")["errors"][0]["code"] == "STRUCTURE_INVALID"
    assert validate_iban("NLX1ABNA0417164300")["errors"][0]["code"] == "STRUCTURE_INVALID"
    assert validate_iban("1291ABNA0417164300")["errors"][0]["code"] == "STRUCTURE_INVALID"


def test_validate_iban_error_paths_per_code():
    assert validate_iban("XX00INVALID")["errors"][0]["code"] == "COUNTRY_NOT_SUPPORTED"
    r_len = validate_iban("NL91ABNA041716430")
    assert r_len["errors"][0]["code"] == "LENGTH_MISMATCH"
    assert r_len["expected_length"] == 18
    assert r_len["length"] == 17
    r_bban = validate_iban("NL9112340417164300")
    assert r_bban["errors"][0]["code"] == "BBAN_FORMAT_INVALID"
    assert r_bban["checks"]["length"] is True
    r_sum = validate_iban("NL91ABNA0417164301")
    assert r_sum["errors"][0]["code"] == "CHECKSUM_FAILED"
    assert r_sum["checks"]["bban_format"] is True
    assert r_sum["checks"]["mod97"] is False


def test_make_error_rejects_unknown_code():
    assert make_error("EMPTY_INPUT", "x") == {"code": "EMPTY_INPUT", "message": "x"}
    with pytest.raises(ValueError):
        make_error("NOPE", "x")


def test_get_country_is_case_insensitive_and_returns_none():
    assert get_country("nl")["country_name"] == "Netherlands"
    assert get_country(" de ")["iban_length"] == 22
    assert get_country("ZZ") is None
    assert get_country(None) is None


def test_reset_state_restores_registry():
    IBAN_REGISTRY["ZZ"] = {"country_name": "Testland", "iban_length": 10, "bban_pattern": "^[0-9]{6}$", "bank_code_slice": [4, 7], "sepa": False, "example": "ZZ00123456"}
    reset_state()
    assert "ZZ" not in IBAN_REGISTRY
    assert "NL" in IBAN_REGISTRY
