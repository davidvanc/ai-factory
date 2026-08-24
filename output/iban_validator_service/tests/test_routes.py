import pytest
from src.iban_registry import IBAN_REGISTRY, reset_state
from src.logic import MAX_BULK_ITEMS, STANDARDS


@pytest.fixture(autouse=True)
def _reset():
    reset_state()
    yield
    reset_state()


def test_validate_valid_nl_iban(client, auth_headers):
    response = client.post(
        "/validate",
        json={"iban": "NL91ABNA0417164300"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is True
    assert body["iban"] == "NL91ABNA0417164300"
    assert body["formatted"] == "NL91 ABNA 0417 1643 00"
    assert body["country_code"] == "NL"
    assert body["country_name"] == "Netherlands"
    assert body["check_digits"] == "91"
    assert body["bban"] == "ABNA0417164300"
    assert body["length"] == 18
    assert body["expected_length"] == 18
    assert body["bank_code"] == "ABNA"
    assert body["account_number"] == "0417164300"
    assert body["checks"] == {
        "structure": True,
        "country_supported": True,
        "length": True,
        "bban_format": True,
        "mod97": True,
    }
    assert body["errors"] == []


def test_validate_normalizes_lowercase_and_whitespace(client, auth_headers):
    response = client.post(
        "/validate",
        json={"iban": " nl91\tabna 0417\t1643 00 "},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is True
    assert body["iban"] == "NL91ABNA0417164300"
    assert body["formatted"] == "NL91 ABNA 0417 1643 00"
    assert body["input"] == " nl91\tabna 0417\t1643 00 "


def test_validate_checksum_failed(client, auth_headers):
    response = client.post(
        "/validate",
        json={"iban": "NL91ABNA0417164301"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is False
    assert body["errors"][0]["code"] == "CHECKSUM_FAILED"
    assert body["checks"]["bban_format"] is True
    assert body["checks"]["mod97"] is False


def test_validate_length_mismatch(client, auth_headers):
    response = client.post(
        "/validate",
        json={"iban": "NL91ABNA041716430"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is False
    assert body["errors"][0]["code"] == "LENGTH_MISMATCH"
    assert body["length"] == 17
    assert body["expected_length"] == 18
    assert body["checks"]["length"] is False


def test_validate_country_not_supported(client, auth_headers):
    response = client.post(
        "/validate",
        json={"iban": "XX00INVALID"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is False
    assert body["errors"][0]["code"] == "COUNTRY_NOT_SUPPORTED"
    assert body["country_code"] == "XX"
    assert body["country_name"] is None
    assert body["expected_length"] is None
    assert body["checks"]["country_supported"] is False
    assert body["checks"]["structure"] is True


def test_validate_bban_format_invalid(client, auth_headers):
    response = client.post(
        "/validate",
        json={"iban": "NL9112340417164300"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is False
    assert body["errors"][0]["code"] == "BBAN_FORMAT_INVALID"
    assert body["checks"]["length"] is True
    assert body["checks"]["bban_format"] is False


def test_validate_invalid_characters(client, auth_headers):
    response = client.post(
        "/validate",
        json={"iban": "NL91-ABNA-0417-1643-00"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is False
    assert body["errors"][0]["code"] == "INVALID_CHARACTERS"
    assert body["checks"]["structure"] is False


def test_validate_missing_field_returns_422(client, auth_headers):
    response = client.post("/validate", json={}, headers=auth_headers)
    assert response.status_code == 422
    response = client.post(
        "/validate", json={"iban": "XX00INVALID"}, headers=auth_headers
    )
    assert response.status_code == 200


def test_format_print_and_electronic(client, auth_headers):
    response = client.post(
        "/format",
        json={"iban": "nl91abna0417164300", "style": "print"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["formatted"] == "NL91 ABNA 0417 1643 00"
    assert body["electronic"] == "NL91ABNA0417164300"
    assert body["valid"] is True
    assert body["errors"] == []
    assert body["style"] == "print"
    assert body["input"] == "nl91abna0417164300"
    response = client.post(
        "/format",
        json={"iban": "NL91 ABNA 0417 1643 00", "style": "electronic"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["formatted"] == "NL91ABNA0417164300"
    assert body["electronic"] == "NL91ABNA0417164300"


def test_format_unknown_style_returns_422(client, auth_headers):
    response = client.post(
        "/format",
        json={"iban": "NL91ABNA0417164300", "style": "fancy"},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_format_invalid_checksum_still_formats(client, auth_headers):
    response = client.post(
        "/format",
        json={"iban": "NL91ABNA0417164301", "style": "print"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["formatted"] == "NL91 ABNA 0417 1643 01"
    assert body["valid"] is False
    assert body["errors"][0]["code"] == "CHECKSUM_FAILED"


def test_generate_check_digits_nl(client, auth_headers):
    response = client.post(
        "/generate-check-digits",
        json={"country_code": "NL", "bban": "ABNA0417164300"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["check_digits"] == "91"
    assert body["iban"] == "NL91ABNA0417164300"
    assert body["formatted"] == "NL91 ABNA 0417 1643 00"
    assert body["valid"] is True
    assert body["errors"] == []
    assert body["country_code"] == "NL"
    assert body["bban"] == "ABNA0417164300"


def test_generate_check_digits_de(client, auth_headers):
    response = client.post(
        "/generate-check-digits",
        json={"country_code": "de", "bban": "370400440532013000"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["check_digits"] == "89"
    assert body["iban"] == "DE89370400440532013000"
    assert body["valid"] is True


def test_generate_check_digits_repairs_existing_iban(client, auth_headers):
    response = client.post(
        "/generate-check-digits",
        json={"iban": "NL00ABNA0417164300"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["check_digits"] == "91"
    assert body["iban"] == "NL91ABNA0417164300"
    assert body["valid"] is True
    assert body["country_code"] == "NL"
    assert body["bban"] == "ABNA0417164300"


def test_generate_check_digits_missing_input_returns_422(client, auth_headers):
    response = client.post("/generate-check-digits", json={}, headers=auth_headers)
    assert response.status_code == 422


def test_countries_returns_all_entries(client, auth_headers):
    response = client.get("/countries", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == len(IBAN_REGISTRY)
    assert body["count"] > 0
    assert len(body["countries"]) == body["count"]
    assert "NL" in [c["country_code"] for c in body["countries"]]


def test_countries_filter_is_case_insensitive(client, auth_headers):
    response = client.get("/countries?country=nl", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    entry = body["countries"][0]
    assert entry == {
        "country_code": "NL",
        "country_name": "Netherlands",
        "iban_length": 18,
        "bban_pattern": "^[A-Z]{4}[0-9]{10}$",
        "bank_code_slice": [4, 8],
        "sepa": True,
        "example": "NL91ABNA0417164300",
    }


def test_countries_unknown_country_returns_empty(client, auth_headers):
    response = client.get("/countries?country=ZZ", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 0
    assert body["countries"] == []


def test_status_endpoint(client, auth_headers):
    response = client.get("/status", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["countries_supported"] > 0
    assert body["countries_supported"] == len(IBAN_REGISTRY)
    assert body["max_bulk_items"] == MAX_BULK_ITEMS
    assert body["standards"] == list(STANDARDS)
    assert "ISO 13616" in body["standards"]
    assert isinstance(body["version"], str)
    assert body["version"] != ""
