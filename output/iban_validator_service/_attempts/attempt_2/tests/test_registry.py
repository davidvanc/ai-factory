import re
import pytest
from src.iban_registry import IBAN_REGISTRY, reset_state
from src.logic import compute_mod97, validate_iban

@pytest.fixture(autouse=True)
def _reset():
    reset_state()
    yield
    reset_state()

def test_registry_is_not_empty_and_has_core_countries():
    assert len(IBAN_REGISTRY) > 0
    assert "NL" in IBAN_REGISTRY
    assert "DE" in IBAN_REGISTRY
    assert "GB" in IBAN_REGISTRY

def test_every_entry_has_required_keys_and_types():
    required_keys = {"country_name", "iban_length", "bban_pattern", "bank_code_slice", "sepa", "example"}
    for code, entry in IBAN_REGISTRY.items():
        assert set(entry.keys()) == required_keys
        assert isinstance(code, str) and len(code) == 2 and code == code.upper() and code.isalpha()
        assert isinstance(entry["country_name"], str) and entry["country_name"] != ""
        assert isinstance(entry["iban_length"], int) and 15 <= entry["iban_length"] <= 34
        assert isinstance(entry["bban_pattern"], str) and entry["bban_pattern"].startswith("^") and entry["bban_pattern"].endswith("$")
        assert isinstance(entry["sepa"], bool)
        slice_ = entry["bank_code_slice"]
        assert len(slice_) == 2
        assert all(isinstance(x, int) for x in slice_)
        assert 4 <= slice_[0] < slice_[1] <= entry["iban_length"]

def test_every_example_length_matches_iban_length():
    for code, entry in IBAN_REGISTRY.items():
        assert len(entry["example"]) == entry["iban_length"], f"Voor {code}: lengte {len(entry['example'])} != {entry['iban_length']}"
        assert entry["example"][:2] == code
        assert entry["example"] == entry["example"].upper()
        assert entry["example"][2:4].isdigit()

def test_every_example_passes_mod97():
    for code, entry in IBAN_REGISTRY.items():
        assert compute_mod97(entry["example"]) == 1, f"Voor {code}: mod-97 checksum faalt"

def test_every_example_matches_own_bban_pattern():
    for code, entry in IBAN_REGISTRY.items():
        bban = entry["example"][4:]
        assert re.match(entry["bban_pattern"], bban) is not None, f"Voor {code}: BBAN '{bban}' past niet op patroon {entry['bban_pattern']}"

def test_every_example_validates_via_validate_iban():
    for code, entry in IBAN_REGISTRY.items():
        result = validate_iban(entry["example"])
        assert result["valid"] is True, f"Voor {code}: validatie faalt"
        assert result["country_code"] == code
        assert result["expected_length"] == entry["iban_length"]
        assert result["errors"] == []
