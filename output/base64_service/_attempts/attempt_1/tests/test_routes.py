import json
import pytest
from src.models import ALPHABETS, MAX_INPUT_BYTES, SERVICE_NAME, SERVICE_VERSION

ROUNDTRIP_TEXTS = [
    "",
    "a",
    "Hallo wereld",
    "caf\u00e9 \u2713",
    "\U0001F389 feest \U0001F680",
    "\u00c6r\u00f8sk\u00f8bing",
    "regel1\nregel2\ttab",
    "0123456789+/=",
]

def test_encode_hallo_wereld(client, auth_headers) -> None:
    response = client.post("/encode", json={"text": "Hallo wereld", "url_safe": False, "strip_padding": False}, headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == {"encoded": "SGFsbG8gd2VyZWxk", "input_length": 12, "output_length": 16, "url_safe": False, "padding_stripped": False}

def test_encode_lege_string(client, auth_headers) -> None:
    response = client.post("/encode", json={"text": ""}, headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == {"encoded": "", "input_length": 0, "output_length": 0, "url_safe": False, "padding_stripped": False}

def test_encode_unicode_tekst(client, auth_headers) -> None:
    response = client.post("/encode", json={"text": "caf\u00e9 \u2713"}, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["encoded"] == "Y2Fmw6kg4pyT"
    assert data["input_length"] == 6
    assert data["output_length"] == 12
    assert data["url_safe"] is False
    assert data["padding_stripped"] is False

def test_encode_defaults_zonder_optionele_velden(client, auth_headers) -> None:
    response = client.post("/encode", json={"text": "a"}, headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == {"encoded": "YQ==", "input_length": 1, "output_length": 4, "url_safe": False, "padding_stripped": False}

def test_encode_url_safe_gebruikt_dash_en_underscore(client, auth_headers) -> None:
    standaard = client.post("/encode", json={"text": "\u00ff\u00ff\u00fe"}, headers=auth_headers)
    urlsafe = client.post("/encode", json={"text": "\u00ff\u00ff\u00fe", "url_safe": True}, headers=auth_headers)
    assert standaard.status_code == 200 and urlsafe.status_code == 200
    assert standaard.json()["encoded"] == "w7/Dv8O+"
    assert urlsafe.json()["encoded"] == "w7_Dv8O-"
    assert "-" in urlsafe.json()["encoded"] and "_" in urlsafe.json()["encoded"]
    assert "+" not in urlsafe.json()["encoded"] and "/" not in urlsafe.json()["encoded"]
    assert urlsafe.json()["url_safe"] is True

def test_encode_strip_padding_verwijdert_isgelijk_tekens(client, auth_headers) -> None:
    response = client.post("/encode", json={"text": "a", "strip_padding": True}, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "=" not in data["encoded"]
    assert data["encoded"] == "YQ"
    assert data["input_length"] == 1 and data["output_length"] == 2
    assert data["padding_stripped"] is True

def test_encode_strip_padding_zonder_padding_meldt_false(client, auth_headers) -> None:
    response = client.post("/encode", json={"text": "Hallo wereld", "strip_padding": True}, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["encoded"] == "SGFsbG8gd2VyZWxk"
    assert response.json()["padding_stripped"] is False

def test_encode_zonder_text_veld_geeft_422(client, auth_headers) -> None:
    response = client.post("/encode", json={}, headers=auth_headers)
    assert response.status_code == 422
    body = response.json()
    assert "detail" in body
    assert "text" in json.dumps(body)

def test_encode_url_safe_verkeerd_type_geeft_422(client, auth_headers) -> None:
    response = client.post("/encode", json={"text": "a", "url_safe": "yes"}, headers=auth_headers)
    assert response.status_code == 422
    assert "url_safe" in json.dumps(response.json())

def test_decode_hallo_wereld(client, auth_headers) -> None:
    response = client.post("/decode", json={"data": "SGFsbG8gd2VyZWxk", "url_safe": False}, headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == {"decoded": "Hallo wereld", "input_length": 16, "output_length": 12, "url_safe": False, "padding_added": 0}

def test_decode_zonder_padding_rapporteert_padding_added(client, auth_headers) -> None:
    response = client.post("/decode", json={"data": "YQ"}, headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == {"decoded": "a", "input_length": 2, "output_length": 1, "url_safe": False, "padding_added": 2}
    response2 = client.post("/decode", json={"data": "SGFsbG8"}, headers=auth_headers)
    assert response2.status_code == 200
    assert response2.json() == {"decoded": "Hallo", "input_length": 7, "output_length": 5, "url_safe": False, "padding_added": 1}

def test_decode_url_safe(client, auth_headers) -> None:
    response = client.post("/decode", json={"data": "w7_Dv8O-", "url_safe": True}, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["decoded"] == "\u00ff\u00ff\u00fe"
    assert data["url_safe"] is True
    assert data["padding_added"] == 0
    assert data["input_length"] == 8 and data["output_length"] == 3

def test_decode_ongeldige_tekens_geeft_422(client, auth_headers) -> None:
    response = client.post("/decode", json={"data": "abc$$$"}, headers=auth_headers)
    assert response.status_code == 422
    body = response.json()
    assert body["error"] == "invalid_base64_character"
    assert "ongeldige base64" in body["message"]
    assert "'$'" in body["message"]
    assert "3" in body["message"]
    assert "positie 3" in body["detail"]

def test_decode_ongeldige_lengte_geeft_422(client, auth_headers) -> None:
    response = client.post("/decode", json={"data": "SGFsbG8gd2VyZWxka"}, headers=auth_headers)
    assert response.status_code == 422
    body = response.json()
    assert body["error"] == "invalid_base64_length"
    assert "ongeldige base64" in body["message"] and "17" in body["message"]
    assert "deelbaar is door 4" in body["detail"]

def test_decode_discontinue_padding_geeft_422(client, auth_headers) -> None:
    response = client.post("/decode", json={"data": "SG=s"}, headers=auth_headers)
    assert response.status_code == 422
    body = response.json()
    assert body["error"] == "invalid_base64"
    assert "ongeldige base64" in body["message"]
    assert body["detail"] != ""

def test_decode_niet_utf8_geeft_422(client, auth_headers) -> None:
    response = client.post("/decode", json={"data": "//8="}, headers=auth_headers)
    assert response.status_code == 422
    body = response.json()
    assert body["error"] == "non_utf8_payload"
    assert "UTF-8" in body["message"]
    assert "niet-tekstuele" in body["message"]
    assert "byte-positie" in body["detail"]

def test_decode_verkeerd_type_geeft_422(client, auth_headers) -> None:
    response = client.post("/decode", json={"data": 12345}, headers=auth_headers)
    assert response.status_code == 422
    assert "data" in json.dumps(response.json())

def test_encode_te_grote_invoer_geeft_413(client, auth_headers) -> None:
    te_groot = "a" * (MAX_INPUT_BYTES + 1)
    response = client.post("/encode", json={"text": te_groot}, headers=auth_headers)
    assert response.status_code == 413
    body = response.json()
    assert body["error"] == "input_too_large"
    assert "maximum" in body["message"]
    assert str(MAX_INPUT_BYTES) in body["message"]
    assert str(MAX_INPUT_BYTES) in body["detail"]
    assert set(body.keys()) == {"error", "message", "detail"}

def test_decode_te_grote_invoer_geeft_413(client, auth_headers) -> None:
    te_groot = "A" * (MAX_INPUT_BYTES + 1)
    response = client.post("/decode", json={"data": te_groot}, headers=auth_headers)
    assert response.status_code == 413
    body = response.json()
    assert body["error"] == "input_too_large"
    assert "maximum" in body["message"] and str(MAX_INPUT_BYTES) in body["message"]

@pytest.mark.parametrize("text", ROUNDTRIP_TEXTS)
def test_roundtrip_via_http(client, auth_headers, text) -> None:
    enc = client.post("/encode", json={"text": text}, headers=auth_headers)
    assert enc.status_code == 200
    encoded = enc.json()["encoded"]
    dec = client.post("/decode", json={"data": encoded}, headers=auth_headers)
    assert dec.status_code == 200
    assert dec.json()["decoded"] == text
    assert dec.json()["output_length"] == len(text)

@pytest.mark.parametrize("text", ROUNDTRIP_TEXTS)
def test_roundtrip_url_safe_zonder_padding_via_http(client, auth_headers, text) -> None:
    enc = client.post("/encode", json={"text": text, "url_safe": True, "strip_padding": True}, headers=auth_headers)
    assert enc.status_code == 200
    encoded = enc.json()["encoded"]
    assert "=" not in encoded
    dec = client.post("/decode", json={"data": encoded, "url_safe": True}, headers=auth_headers)
    assert dec.status_code == 200
    assert dec.json()["decoded"] == text
    assert dec.json()["padding_added"] in (0, 1, 2)

def test_status_endpoint(client, auth_headers) -> None:
    response = client.get("/status", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == SERVICE_NAME
    assert body["version"] == SERVICE_VERSION
    assert body["alphabets"] == ALPHABETS
    assert body["alphabets"] == ["standard", "url_safe"]
    assert body["max_input_bytes"] == MAX_INPUT_BYTES
    assert set(body.keys()) == {"status", "service", "version", "alphabets", "max_input_bytes"}

@pytest.mark.parametrize(
    "payload",
    [
        {"data": "abc$$$"},
        {"data": "SGFsbG8gd2VyZWxka"},
        {"data": "SG=s"},
        {"data": "//8="},
    ],
)
def test_foutantwoord_is_altijd_json_met_error_message_detail(client, auth_headers, payload) -> None:
    response = client.post("/decode", json=payload, headers=auth_headers)
    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/json")
    body = response.json()
    assert set(body.keys()) == {"error", "message", "detail"}
    assert isinstance(body["error"], str) and body["error"] != ""
    assert isinstance(body["message"], str) and body["message"] != ""
    assert isinstance(body["detail"], str) and body["detail"] != ""
