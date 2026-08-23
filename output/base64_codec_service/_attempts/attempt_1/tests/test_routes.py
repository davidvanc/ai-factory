import random
import pytest
from src import config
from src import logic

@pytest.fixture(autouse=True)
def _reset_state():
    logic.reset_state()
    yield
    logic.reset_state()

def test_encode_hallo_wereld(client, auth_headers):
    r = client.post("/encode", json={"text": "Hallo wereld", "url_safe": False, "encoding": "utf-8"}, headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body == {"encoded": "SGFsbG8gd2VyZWxk", "input_bytes": 12, "output_length": 16, "url_safe": False, "encoding": "utf-8"}

def test_encode_url_safe_alfabet(client, auth_headers):
    r = client.post("/encode", json={"text": "~~~~~?", "url_safe": True}, headers=auth_headers)
    assert r.status_code == 200
    encoded = r.json()["encoded"]
    assert encoded == "fn5-fn4_"
    assert "+" not in encoded and "/" not in encoded
    assert r.json()["url_safe"] is True

def test_encode_unicode_en_roundtrip(client, auth_headers):
    r = client.post("/encode", json={"text": "café ☕"}, headers=auth_headers)
    assert r.status_code == 200 and r.json()["encoded"] == "Y2Fmw6kg4piV"
    r2 = client.post("/decode", json={"data": "Y2Fmw6kg4piV"}, headers=auth_headers)
    assert r2.status_code == 200 and r2.json()["decoded"] == "café ☕"

def test_encode_zonder_text_veld_422(client, auth_headers):
    r = client.post("/encode", json={"url_safe": False}, headers=auth_headers)
    assert r.status_code == 422
    body = r.json()
    assert body["error_code"] == "MISSING_FIELD" and "text" in body["message"]

def test_encode_lege_string_422(client, auth_headers):
    r = client.post("/encode", json={"text": ""}, headers=auth_headers)
    assert r.status_code == 422 and r.json()["error_code"] == "EMPTY_INPUT"

def test_encode_verkeerd_type_text_422(client, auth_headers):
    r = client.post("/encode", json={"text": 123}, headers=auth_headers)
    assert r.status_code == 422
    assert r.json()["error_code"] == "VALIDATION_ERROR" and "text" in r.json()["message"]

def test_encode_te_grote_payload(client, auth_headers):
    groot = "a" * (config.MAX_INPUT_BYTES + 1)
    r = client.post("/encode", json={"text": groot}, headers=auth_headers)
    assert r.status_code in (413, 422)
    assert r.json()["error_code"] == "INPUT_TOO_LARGE"

def test_encode_onbekende_encoding_422(client, auth_headers):
    r = client.post("/encode", json={"text": "a", "encoding": "klingon"}, headers=auth_headers)
    assert r.status_code == 422 and r.json()["error_code"] == "UNSUPPORTED_ENCODING"

def test_decode_basis(client, auth_headers):
    r = client.post("/decode", json={"data": "SGFsbG8gd2VyZWxk", "encoding": "utf-8", "strict": True}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json() == {"decoded": "Hallo wereld", "input_length": 16, "output_bytes": 12, "encoding": "utf-8", "detected_alphabet": "standard"}

def test_decode_tolerant_voor_whitespace(client, auth_headers):
    r = client.post("/decode", json={"data": "SGFsbG8g\nd2Vy ZWxk"}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["decoded"] == "Hallo wereld" and r.json()["input_length"] == 16

def test_decode_ongeldig_teken_400(client, auth_headers):
    r = client.post("/decode", json={"data": "SGVsbG8=!!"}, headers=auth_headers)
    assert r.status_code == 400
    body = r.json()
    assert body["error_code"] == "INVALID_BASE64_CHARACTER" and body["position"] == 8
    assert "'!'" in body["message"]

def test_decode_verkeerde_padding_400(client, auth_headers):
    r = client.post("/decode", json={"data": "SGVsbG8"}, headers=auth_headers)
    assert r.status_code == 400
    body = r.json()
    assert body["error_code"] == "INVALID_PADDING" and "deelbaar door 4" in body["message"]

def test_decode_niet_utf8_400(client, auth_headers):
    r = client.post("/decode", json={"data": "/w==", "strict": True}, headers=auth_headers)
    assert r.status_code == 400
    assert r.json()["error_code"] == "NOT_DECODABLE_TEXT" and r.json()["position"] == 0

def test_decode_url_safe_detected_alphabet(client, auth_headers):
    r = client.post("/decode", json={"data": "fn5-fn4_"}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["decoded"] == "~~~~~?" and r.json()["detected_alphabet"] == "url_safe"

def test_decode_zonder_data_veld_422(client, auth_headers):
    r = client.post("/decode", json={}, headers=auth_headers)
    assert r.status_code == 422
    assert r.json()["error_code"] == "MISSING_FIELD" and "data" in r.json()["message"]

def test_validate_geldige_base64(client, auth_headers):
    r = client.post("/validate", json={"data": "SGFsbG8gd2VyZWxk"}, headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["valid"] is True and body["error_code"] is None and body["position"] is None
    assert body["detected_alphabet"] == "standard"

def test_validate_ongeldige_base64_blijft_200(client, auth_headers):
    r = client.post("/validate", json={"data": "SGFsbG8gd2VyZWxk!!"}, headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["valid"] is False and body["error_code"] == "INVALID_BASE64_CHARACTER"
    assert body["position"] == 16 and "'!'" in body["message"]

def test_status_endpoint(client, auth_headers):
    r = client.get("/status", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["service"] == config.SERVICE_NAME
    assert body["version"] == config.SERVICE_VERSION
    assert body["supported_alphabets"] == ["standard", "url_safe"]
    assert body["max_input_bytes"] == config.MAX_INPUT_BYTES

def test_status_counters_lopen_mee(client, auth_headers):
    client.post("/encode", json={"text": "a"}, headers=auth_headers)
    client.post("/validate", json={"data": "SGVsbG8="}, headers=auth_headers)
    body = client.get("/status", headers=auth_headers).json()
    assert body["counters"]["encode"] == 1
    assert body["counters"]["validate"] == 1
    assert body["counters"]["total"] == 2

def test_alle_foutresponses_zelfde_schema(client, auth_headers):
    gevallen = [
        ("/encode", {}),
        ("/encode", {"text": ""}),
        ("/encode", {"text": "a", "encoding": "klingon"}),
        ("/decode", {"data": "SGVsbG8=!!"}),
        ("/decode", {"data": "SGVsbG8"}),
        ("/decode", {"data": "/w=="}),
        ("/validate", {}),
    ]
    for pad, payload in gevallen:
        r = client.post(pad, json=payload, headers=auth_headers)
        assert r.status_code >= 400
        body = r.json()
        assert set(body.keys()) == {"error_code", "message", "detail", "position"}
        assert isinstance(body["error_code"], str) and body["error_code"] != ""
        assert isinstance(body["message"], str) and body["message"] != ""
        assert body["detail"] is None or isinstance(body["detail"], str)
        assert body["position"] is None or isinstance(body["position"], int)

def test_verkeerd_content_type_422(client, auth_headers):
    headers = dict(auth_headers)
    headers["Content-Type"] = "text/plain"
    r = client.post("/encode", content="dit is geen json", headers=headers)
    assert r.status_code == 422
    body = r.json()
    assert body["error_code"] == "INVALID_CONTENT_TYPE" and "application/json" in body["message"]

def test_niet_json_body_422(client, auth_headers):
    headers = dict(auth_headers)
    headers["Content-Type"] = "application/json"
    r = client.post("/encode", content="{ongeldig json", headers=headers)
    assert r.status_code == 422
    body = r.json()
    assert body["error_code"] == "INVALID_JSON" and isinstance(body["detail"], str)

def test_json_body_geen_object_422(client, auth_headers):
    headers = dict(auth_headers)
    headers["Content-Type"] = "application/json"
    r = client.post("/decode", content='"alleen een string"', headers=headers)
    assert r.status_code == 422 and r.json()["error_code"] == "INVALID_JSON"

def test_roundtrip_property_via_http(client, auth_headers):
    random.seed(7)
    pool = "abcXYZ019 ~?!+/-_\n\téàß☕日"
    teksten = ["Hallo wereld", "café ☕", "~~~~~?"] + ["".join(random.choice(pool) for _ in range(random.randint(1, 30))) for _ in range(15)]
    for tekst in teksten:
        enc = client.post("/encode", json={"text": tekst}, headers=auth_headers)
        assert enc.status_code == 200
        dec = client.post("/decode", json={"data": enc.json()["encoded"]}, headers=auth_headers)
        assert dec.status_code == 200
        assert dec.json()["decoded"] == tekst
