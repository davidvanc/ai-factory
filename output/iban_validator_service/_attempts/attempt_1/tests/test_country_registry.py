import re
import pytest
from src import country_registry
from src.country_registry import all_countries, country_count, get_country, reset_state
from src.logic import mod97, validate_iban


@pytest.fixture(autouse=True)
def _reset_registry():
    reset_state()
    yield
    reset_state()


def test_registry_is_not_empty():
    assert country_count() > 0
    assert country_count() == len(all_countries())


def test_every_entry_has_all_required_keys():
    expected_keys = {
        "country_code",
        "name",
        "iban_length",
        "bban_pattern",
        "bban_regex",
        "sepa",
        "example",
        "bank_length",
        "branch_length",
    }
    for entry in all_countries():
        assert expected_keys.issubset(entry.keys())
        assert isinstance(entry["iban_length"], int)
        assert isinstance(entry["sepa"], bool)
        assert entry["bban_regex"].startswith("^")
        assert entry["bban_regex"].endswith("$")


def test_entry_length_matches_regex_match_of_example():
    for entry in all_countries():
        bban = entry["example"][4:]
        match = re.fullmatch(entry["bban_regex"], bban)
        assert match is not None, f"BBAN regex mismatch for {entry['country_code']}"
        assert entry["iban_length"] == 4 + len(match.group(0))
        assert len(entry["example"]) == entry["iban_length"]


def test_every_example_has_mod97_equal_to_one():
    for entry in all_countries():
        assert mod97(entry["example"]) == 1, f"mod97 failed for {entry['country_code']}"


def test_every_example_validates_via_logic():
    for entry in all_countries():
        res = validate_iban(entry["example"])
        assert res["valid"] is True, f"Validation failed for {entry['country_code']}"
        assert res["errors"] == []
        assert res["country_code"] == entry["country_code"]
        assert res["expected_length"] == entry["iban_length"]


def test_bank_and_branch_lengths_fit_in_bban():
    for entry in all_countries():
        bban_len = entry["iban_length"] - 4
        assert entry["bank_length"] >= 1
        assert entry["branch_length"] >= 0
        assert entry["bank_length"] + entry["branch_length"] < bban_len


def test_get_country_is_case_insensitive_and_strips():
    assert get_country("be")["iban_length"] == 16
    assert get_country("BE")["country_code"] == "BE"
    assert get_country(" nl ")["country_code"] == "NL"


def test_get_country_unknown_returns_none():
    assert get_country("ZZ") is None
    assert get_country("") is None
    assert get_country(None) is None
    assert get_country(123) is None


def test_all_countries_is_sorted_by_country_code():
    codes = [e["country_code"] for e in all_countries()]
    assert codes == sorted(codes)


def test_reset_state_removes_added_entry():
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
    assert get_country("QQ") is not None
    reset_state()
    assert get_country("QQ") is None
    assert country_count() == len(all_countries())
