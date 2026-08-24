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
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "iban_validator_service"
    assert body["spec"] == "ISO 13616 / ISO 7064 mod-97-10"
    assert isinstance(body["version"], str) and body["version"] != ""
    assert body["supported_countries"] > 0
    assert body["supported_countries"] == country_registry.country_count()


def test_post_validate_valid_nl(client):
    response = client.post("/validate", json={"iban": "NL91ABNA0417164300"})
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is True
    assert body["errors"] == []
    assert body["country_code"] == "NL"
    assert body["check_digits"] == "91"
    assert body["bban"] == "ABNA0417164300"
    assert body["length"] == 18
    assert body["expected_length"] == 18
    assert body["checksum_mod97"] == 1
    assert body["formatted"] == "NL91 ABNA 0417 1643 00"
    assert body["compact"] == "NL91ABNA0417164300"
    assert body["bank_identifier"] == "ABNA"
    assert body["branch_identifier"] is None
    assert body["account_number"] == "0417164300"
    assert body["input"] == "NL91ABNA0417164300"


def test_post_validate_normalizes_spaces_and_lowercase(client):
    response = client.post("/validate", json={"iban": "nl91 abna 0417 1643 00"})
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is True
    assert body["compact"] == "NL91ABNA0417164300"
    assert body["formatted"] == "NL91 ABNA 0417 1643 00"
    assert body["input"] == "nl91 abna 0417 1643 00"
    assert body["errors"] == []


def test_post_validate_checksum_failed(client):
    response = client.post("/validate", json={"iban": "NL91ABNA0417164301"})
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is False
    assert codes(body) == ["CHECKSUM_FAILED"]
    assert body["length"] == 18
    assert body["expected_length"] == 18
    assert body["checksum_mod97"] != 1


def test_post_validate_invalid_length(client):
    response = client.post("/validate", json={"iban": "FR761234"})
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is False
    assert codes(body) == ["INVALID_LENGTH"]
    assert body["expected_length"] == 27
    assert body["length"] == 8
    assert body["country_code"] == "FR"
    assert body["formatted"] == "FR76 1234"


def test_post_validate_unknown_country(client):
    response = client.post("/validate", json={"iban": "XX00INVALID"})
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is False
    assert codes(body) == ["UNKNOWN_COUNTRY"]
    assert body["country_code"] == "XX"
    assert body["expected_length"] is None
    assert body["compact"] == "XX00INVALID"
    assert body["formatted"] == "XX00 INVA LID"


def test_post_validate_invalid_characters(client):
    response = client.post("/validate", json={"iban": "NL91-ABNA*0417"})
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is False
    assert codes(body) == ["INVALID_CHARACTERS"]


def test_post_validate_invalid_format(client):
    response = client.post("/validate", json={"iban": "NL911234041716430A"})
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is False
    assert codes(body) == ["INVALID_FORMAT"]
    assert body["country_code"] == "NL"
    assert body["length"] == 18
    assert body["expected_length"] == 18


def test_post_validate_forbidden_check_digits(client):
    for cd in ("00", "01", "99"):
        iban = f"NL{cd}ABNA0417164300"
        response = client.post("/validate", json={"iban": iban})
        assert response.status_code == 200
        body = response.json()
        assert body["valid"] is False
        assert codes(body) == ["INVALID_CHECK_DIGITS"]
        assert body["check_digits"] == iban[2:4]


def test_get_validate_matches_post_validate(client):
    get_response = client.get("/validate?iban=DE89370400440532013000")
    post_response = client.post("/validate", json={"iban": "DE89370400440532013000"})
    assert get_response.status_code == 200
    assert post_response.status_code == 200
    get_body = get_response.json()
    post_body = post_response.json()
    assert get_body == post_body
    assert get_body["valid"] is True
    assert get_body["country_code"] == "DE"
    assert get_body["check_digits"] == "89"
    assert get_body["bban"] == "370400440532013000"
    assert get_body["length"] == 22
    assert get_body["expected_length"] == 22
    assert get_body["checksum_mod97"] == 1
    assert get_body["formatted"] == "DE89 3704 0044 0532 0130 00"
    assert get_body["bank_identifier"] == "37040044"
    assert get_body["branch_identifier"] is None
    assert get_body["account_number"] == "0532013000"
    assert get_body["errors"] == []


def test_post_validate_missing_field_returns_422(client):
    response = client.post("/validate", json={})
    assert response.status_code == 422


def test_get_validate_without_query_returns_422(client):
    response = client.get("/validate")
    assert response.status_code == 422


def test_post_format_print_style(client):
    response = client.post("/format", json={"iban": "nl91abna0417164300", "style": "print"})
    assert response.status_code == 200
    body = response.json()
    assert body["formatted"] == "NL91 ABNA 0417 1643 00"
    assert body["compact"] == "NL91ABNA0417164300"
    assert body["style"] == "print"
    assert body["valid"] is True
    assert body["errors"] == []
    assert body["input"] == "nl91abna0417164300"


def test_post_format_compact_style(client):
    response = client.post("/format", json={"iban": "de89 3704 0044 0532 0130 00", "style": "compact"})
    assert response.status_code == 200
    body = response.json()
    assert body["formatted"] == "DE89370400440532013000"
    assert body["compact"] == "DE89370400440532013000"
    assert body["style"] == "compact"
    assert body["valid"] is True


def test_post_format_electronic_is_alias_of_compact(client):
    response = client.post("/format", json={"iban": "nl91 abna 0417 1643 00", "style": "electronic"})
    assert response.status_code == 200
    body = response.json()
    assert body["formatted"] == "NL91ABNA0417164300"
    assert body["style"] == "electronic"


def test_post_format_unknown_style_returns_422(client):
    response = client.post("/format", json={"iban": "NL91ABNA0417164300", "style": "banana"})
    assert response.status_code == 422


def test_post_format_formats_invalid_checksum_too(client):
    response = client.post("/format", json={"iban": "NL91ABNA0417164301", "style": "print"})
    assert response.status_code == 200
    body = response.json()
    assert body["formatted"] == "NL91 ABNA 0417 1643 01"
    assert body["valid"] is False
    assert codes(body) == ["CHECKSUM_FAILED"]


def test_get_countries_returns_full_registry(client):
    response = client.get("/countries")
    assert response.status_code == 200
    body = response.json()
    expected_count = country_registry.country_count()
    assert body["count"] == expected_count
    assert len(body["countries"]) == expected_count
    for entry in body["countries"]:
        assert set(entry.keys()) == {
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
        assert entry["iban_length"] > 0
    nl_entry = next(e for e in body["countries"] if e["country_code"] == "NL")
    assert nl_entry["iban_length"] == 18
    assert nl_entry["bban_pattern"] == "4!a10!n"
    assert nl_entry["bban_regex"] == "^[A-Z]{4}[0-9]{10}$"
    assert nl_entry["sepa"] is True
    assert nl_entry["example"] == "NL91ABNA0417164300"


def test_get_country_by_code_is_case_insensitive(client):
    response = client.get("/countries/be")
    assert response.status_code == 200
    body = response.json()
    assert body["country_code"] == "BE"
    assert body["name"] == "Belgium"
    assert body["iban_length"] == 16
    assert body["bban_pattern"] == "12!n"
    assert body["bban_regex"] == "^[0-9]{12}$"
    assert body["sepa"] is True
    assert body["example"] == "BE68539007547034"


def test_get_country_unknown_returns_404(client):
    response = client.get("/countries/ZZ")
    assert response.status_code == 404
