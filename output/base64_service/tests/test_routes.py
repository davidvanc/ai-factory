import pytest
from fastapi import FastAPI
from src.main import app


def test_encode_hallo_wereld(client):
    response = client.post("/encode", json={"text": "Hallo wereld", "url_safe": False, "strip_padding": False})
    assert response.status_code == 200
    assert response.json() == {"input_text": "Hallo wereld", "encoded": "SGFsbG8gd2VyZWxk", "alphabet": "standard", "input_bytes": 12, "output_length": 16}


def test_encode_url_safe_replaces_plus_and_slash(client):
    standard = client.post("/encode", json={"text": "\U0001F600ÿÿ", "url_safe": False}).json()
    assert standard["encoded"] == "8J+YgMO/w78="
    response = client.post("/encode", json={"text": "\U0001F600ÿÿ", "url_safe": True})
    assert response.status_code == 200
    body = response.json()
    assert body["encoded"] == "8J-YgMO_w78="
    assert "+" not in body["encoded"] and "/" not in body["encoded"]
    assert body["alphabet"] == "url_safe"


def test_encode_strip_padding_has_no_equals(client):
    response = client.post("/encode", json={"text": "Hallo", "strip_padding": True})
    assert response.status_code == 200
    body = response.json()
    assert body["encoded"] == "SGFsbG8"
    assert "=" not in body["encoded"]
    assert body["output_length"] == 7


def test_encode_unicode_and_round_trip(client):
    encode_response = client.post("/encode", json={"text": "héllo €"})
    assert encode_response.status_code == 200
    encoded_body = encode_response.json()
    assert encoded_body["encoded"] == "aMOpbGxvIOKCrA=="
    assert encoded_body["input_bytes"] == 10
    decode_response = client.post("/decode", json={"data": encoded_body["encoded"]})
    assert decode_response.status_code == 200
    decoded_body = decode_response.json()
    assert decoded_body["decoded"] == "héllo €"
    assert decoded_body["output_length"] == 7


def test_encode_empty_text_returns_empty_input_error(client):
    response = client.post("/encode", json={"text": ""})
    assert response.status_code == 422
    body = response.json()
    assert body["error_code"] == "EMPTY_INPUT"
    assert isinstance(body["message"], str) and body["message"] != ""
    assert isinstance(body["detail"], str) and body["detail"] != ""


def test_encode_missing_text_field_gives_pydantic_422(client):
    response = client.post("/encode", json={})
    assert response.status_code == 422
    body = response.json()
    assert isinstance(body["detail"], list)
    assert "error_code" not in body


def test_decode_hallo_wereld(client):
    response = client.post("/decode", json={"data": "SGFsbG8gd2VyZWxk", "url_safe": False, "fix_padding": True})
    assert response.status_code == 200
    assert response.json() == {"input_data": "SGFsbG8gd2VyZWxk", "decoded": "Hallo wereld", "alphabet": "standard", "padding_fixed": False, "output_length": 12}


def test_decode_invalid_character(client):
    response = client.post("/decode", json={"data": "SGFsbG8g@d2VyZWxk"})
    assert response.status_code == 422
    body = response.json()
    assert body["error_code"] == "INVALID_BASE64_CHARACTER"
    assert "positie 8" in body["message"]
    assert "'@'" in body["message"]


def test_decode_invalid_padding_without_fix(client):
    response = client.post("/decode", json={"data": "SGFsbG8", "fix_padding": False})
    assert response.status_code == 422
    assert response.json()["error_code"] == "INVALID_PADDING"


def test_decode_padding_fixed_true(client):
    response = client.post("/decode", json={"data": "SGFsbG8", "fix_padding": True})
    assert response.status_code == 200
    body = response.json()
    assert body["decoded"] == "Hallo"
    assert body["padding_fixed"] is True
    assert body["output_length"] == 5
    assert body["input_data"] == "SGFsbG8"


def test_decode_not_utf8(client):
    response = client.post("/decode", json={"data": "//4="})
    assert response.status_code == 422
    body = response.json()
    assert body["error_code"] == "NOT_UTF8_DECODABLE"
    assert "UTF-8" in body["message"]


def test_decode_url_safe_detected(client):
    response = client.post("/decode", json={"data": "8J-YgMO_w78="})
    assert response.status_code == 200
    body = response.json()
    assert body["alphabet"] == "url_safe"
    assert body["decoded"] == "\U0001F600ÿÿ"
    assert body["output_length"] == 3


def test_round_trip_via_api(client):
    for text in ["Hallo wereld", "héllo €", "\U0001F600ÿÿ", "regel1\nregel2", "tab\tend"]:
        encoded = client.post("/encode", json={"text": text}).json()["encoded"]
        decode_response = client.post("/decode", json={"data": encoded})
        assert decode_response.status_code == 200
        assert decode_response.json()["decoded"] == text


def test_validate_valid_base64(client):
    response = client.post("/validate", json={"data": "SGFsbG8gd2VyZWxk"})
    assert response.status_code == 200
    assert response.json() == {"data": "SGFsbG8gd2VyZWxk", "valid": True, "reason": None, "error_code": None}


def test_validate_invalid_base64(client):
    response = client.post("/validate", json={"data": "SGFsbG8g@d2VyZWxk"})
    assert response.status_code == 200
    body = response.json()
    assert body["data"] == "SGFsbG8g@d2VyZWxk"
    assert body["valid"] is False
    assert body["reason"] == "Ongeldig teken '@' op positie 8 voor base64 alfabet"
    assert body["error_code"] == "INVALID_BASE64_CHARACTER"


def test_status_endpoint(client):
    response = client.get("/status")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "base64_service"
    assert body["supported_alphabets"] == ["standard", "url_safe"]
    assert isinstance(body["version"], str) and body["version"] != ""


def test_error_responses_have_consistent_schema(client):
    responses = [client.post("/encode", json={"text": ""}), client.post("/decode", json={"data": "SGFsbG8g@d2VyZWxk"}), client.post("/decode", json={"data": "SGFsbG8", "fix_padding": False}), client.post("/decode", json={"data": "//4="})]
    for response in responses:
        assert response.status_code == 422
        body = response.json()
        assert set(body.keys()) == {"error_code", "message", "detail"}
        assert all(isinstance(body[key], str) and body[key] != "" for key in ("error_code", "message", "detail"))


def test_app_object_and_openapi(client):
    assert isinstance(app, FastAPI)
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/encode" in paths and "/decode" in paths and "/validate" in paths and "/status" in paths
