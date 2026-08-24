import pytest
from src import country_registry


@pytest.fixture(autouse=True)
def _reset_registry():
    country_registry.reset_state()
    yield
    country_registry.reset_state()


def codes(body):
    return [e["code"] for e in body["errors"]]


def test_status_returns_ok_and_metadata(client):
    response = client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "iban_validator_service"
    assert data["spec"] == "ISO 13616 / ISO 7064 mod-97-10"
    assert isinstance(data["version"], str) and data["version"]
    assert data["supported_countries"] > 0
    assert data["supported_countries"] == country_registry.country_count()


def test_post_validate_valid_nl(client):
    response = client.post("/validate", json={"iban": "NL91ABNA0417164300"})
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["errors"] == []
    assert data["country_code"] == "NL"
    assert data["check_digits"] == "91"
    assert data["bban"] == "ABNA0417164300"
    assert data["length"] == 18
    assert data["expected_length"] == 18
    assert data["checksum_mod97"] == 1
    assert data["formatted"] == "NL91 ABNA 0417 1643 00"
    assert data["compact"] == "NL91ABNA0417164300"
    assert data["bank_identifier"] == "ABNA"
    assert data["branch_identifier"] is None
    assert data["account_number"] == "0417164300"
    assert data["input"] == "NL91ABNA0417164300"


def test_post_validate_normalizes_spaces_and_lowercase(client):
    response = client.post("/validate", json={"iban": "nl91 abna 0417 1643 00"})
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["compact"] == "NL91ABNA0417164300"
    assert data["formatted"] == "NL91 ABNA 0417 1643 00"
    assert data["input"] == "nl91 abna 0417 1643 00"
    assert data["errors"] == []


def test_post_validate_checksum_failed(client):
    response = client.post("/validate", json={"iban": "NL91ABNA0417164301"})
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert codes(data) == ["CHECKSUM_FAILED"]
    assert data["length"] == 18
    assert data["expected_length"] == 18
    assert data["checksum_mod97"] != 1


def test_post_validate_invalid_length(client):
    response = client.post("/validate", json={"iban": "FR761234"})
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert codes(data) == ["INVALID_LENGTH"]
    assert data["expected_length"] == 27
    assert data["length"] == 8
    assert data["country_code"] == "FR"
    assert data["formatted"] == "FR76 1234"


def test_post_validate_unknown_country(client):
    response = client.post("/validate", json={"iban": "XX00INVALID"})
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert codes(data) == ["UNKNOWN_COUNTRY"]
    assert data["country_code"] == "XX"
    assert data["expected_length"] is None
    assert data["compact"] == "XX00INVALID"
    assert data["formatted"] == "XX00 INVA LID"


def test_post_validate_invalid_characters(client):
    response = client.post("/validate", json={"iban": "NL91-ABNA*0417"})
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert codes(data) == ["INVALID_CHARACTERS"]


def test_post_validate_invalid_format(client):
    response = client.post("/validate", json={"iban": "NL911234041716430A"})
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert codes(data) == ["INVALID_FORMAT"]
    assert data["country_code"] == "NL"
    assert data["length"] == 18
    assert data["expected_length"] == 18


def test_post_validate_forbidden_check_digits(client):
    for cd in ("00", "01", "99"):
        response = client.post("/validate", json={"iban": f"NL{cd}ABNA0417164300"})
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert codes(data) == ["INVALID_CHECK_DIGITS"]
        assert data["check_digits"] == cd


def test_get_validate_matches_post_validate(client):
    get_resp = client.get("/validate?iban=DE89370400440532013000")
    post_resp = client.post("/validate", json={"iban": "DE89370400440532013000"})
    assert get_resp.status_code == 200
    assert post_resp.status_code == 200
    assert get_resp.json() == post_resp.json()
    data = get_resp.json()
    assert data["valid"] is True
    assert data["country_code"] == "DE"
    assert data["check_digits"] == "89"
    assert data["bban"] == "370400440532013000"
    assert data["length"] == 22
    assert data["expected_length"] == 22
    assert data["checksum_mod97"] == 1
    assert data["formatted"] == "DE89 3704 0044 0532 0130 00"
    assert data["bank_identifier"] == "37040044"
    assert data["branch_identifier"] is None
    assert data["account_number"] == "0532013000"
    assert data["errors"] == []


def test_post_validate_missing_field_returns_422(client):
    response = client.post("/validate", json={})
    assert response.status_code == 422


def test_get_validate_without_query_returns_422(client):
    response = client.get("/validate")
    assert response.status_code == 422


def test_post_format_print_style(client):
    response = client.post("/format", json={"iban": "nl91abna0417164300", "style": "print"})
    assert response.status_code == 200
    data = response.json()
    assert data["formatted"] == "NL91 ABNA 0417 1643 00"
    assert data["compact"] == "NL91ABNA0417164300"
    assert data["style"] == "print"
    assert data["valid"] is True
    assert data["errors"] == []
    assert data["input"] == "nl91abna0417164300"


def test_post_format_compact_style(client):
    response = client.post("/format", json={"iban": "de89 3704 0044 0532 0130 00", "style": "compact"})
    assert response.status_code == 200
    data = response.json()
    assert data["formatted"] == "DE89370400440532013000"
    assert data["compact"] == "DE89370400440532013000"
    assert data["style"] == "compact"
    assert data["valid"] is True


def test_post_format_electronic_is_alias_of_compact(client):
    response = client.post("/format", json={"iban": "nl91 abna 0417 1643 00", "style": "electronic"})
    assert response.status_code == 200
    data = response.json()
    assert data["formatted"] == "NL91ABNA0417164300"
    assert data["style"] == "electronic"


def test_post_format_unknown_style_returns_422(client):
    response = client.post("/format", json={"iban": "NL91ABNA0417164300", "style": "banana"})
    assert response.status_code == 422


def test_post_format_formats_invalid_checksum_too(client):
    response = client.post("/format", json={"iban": "NL91ABNA0417164301", "style": "print"})
    assert response.status_code == 200
    data = response.json()
    assert data["formatted"] == "NL91 ABNA 0417 1643 01"
    assert data["valid"] is False
    assert codes(data) == ["CHECKSUM_FAILED"]


def test_get_countries_returns_full_registry(client):
    response = client.get("/countries")
    assert response.status_code == 200
    data = response.json()
    expected_count = country_registry.country_count()
    assert data["count"] == expected_count
    assert len(data["countries"]) == expected_count
    for entry in data["countries"]:
        assert set(entry.keys()) == {"country_code", "name", "iban_length", "bban_pattern", "bban_regex", "sepa", "example"}
        assert entry["iban_length"] > 0
    nl_entry = next(e for e in data["countries"] if e["country_code"] == "NL")
    assert nl_entry["iban_length"] == 18
    assert nl_entry["bban_pattern"] == "4!a10!n"
    assert nl_entry["bban_regex"] == "^[A-Z]{4}[0-9]{10}$"
    assert nl_entry["sepa"] is True
    assert nl_entry["example"] == "NL91ABNA0417164300"


def test_get_country_by_code_is_case_insensitive(client):
    response = client.get("/countries/be")
    assert response.status_code == 200
    data = response.json()
    assert data["country_code"] == "BE"
    assert data["name"] == "Belgium"
    assert data["iban_length"] == 16
    assert data["bban_pattern"] == "12!n"
    assert data["bban_regex"] == "^[0-9]{12}$"
    assert data["sepa"] is True
    assert data["example"] == "BE68539007547034"


def test_get_country_unknown_returns_404(client):
    response = client.get("/countries/ZZ")
    assert response.status_code == 404
