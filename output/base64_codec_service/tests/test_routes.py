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
    r = client.post(
        "/encode",
        json={"text": "Hallo wereld", "url_safe": False, "encoding": "utf-8"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body == {
        "encoded": "SGFsbG8gd2VyZWxk",
        "input_bytes": 12,
        "output_length": 16,
        "url_safe": False,
        "encoding": "utf-8",
    }


def test_encode_url_safe_alfabet(client, auth_headers):
    r = client.post(
        "/encode",
        json={"text": "~~~~~?", "url_safe": True},
        headers=auth_headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["encoded"] == "fn5-fn4_"
    assert "+" not in body["encoded"]
    assert "/" not in body["encoded"]
    assert body["url_safe"] is True


def test_encode_unicode_en_roundtrip(client, auth_headers):
    r = client.post(
        "/encode",
        json={"text": "café ☕"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["encoded"] == "Y2Fmw6kg4piV"
    r2 = client.post(
        "/decode",
        json={"data": "Y2Fmw6kg4piV"},
        headers=auth_headers,
    )
    assert r2.status_code == 200
    body2 = r2.json()
    assert body2["decoded"] == "café ☕"


def test_encode_zonder_text_veld_422(client, auth_headers):
    r = client.post(
        "/encode",
        json={"url_safe": False},
        headers=auth_headers,
    )
    assert r.status_code == 422
    body = r.json()
    assert body["error_code"] == "MISSING_FIELD"
    assert "text" in body["message"]


def test_encode_lege_string_422(client, auth_headers):
    r = client.post(
        "/encode",
        json={"text": ""},
        headers=auth_headers,
    )
    assert r.status_code == 422
    body = r.json()
    assert body["error_code"] == "EMPTY_INPUT"


def test_encode_verkeerd_type_text_422(client, auth_headers):
    r = client.post(
        "/encode",
        json={"text": 123},
        headers=auth_headers,
    )
    assert r.status_code == 422
    body = r.json()
    assert body["error_code"] == "VALIDATION_ERROR"
    assert "text" in body["message"]


def test_encode_te_grote_payload(client, auth_headers):
    groot = "a" * (config.MAX_INPUT_BYTES + 1)
    r = client.post(
        "/encode",
        json={"text": groot},
        headers=auth_headers,
    )
    assert r.status_code in (413, 422)
    body = r.json()
    assert body["error_code"] == "INPUT_TOO_LARGE"


def test_encode_onbekende_encoding_422(client, auth_headers):
    r = client.post(
        "/encode",
        json={"text": "a", "encoding": "klingon"},
        headers=auth_headers,
    )
    assert r.status_code == 422
    body = r.json()
    assert body["error_code"] == "UNSUPPORTED_ENCODING"


def test_decode_basis(client, auth_headers):
    r = client.post(
        "/decode",
        json={"data": "SGFsbG8gd2VyZWxk", "encoding": "utf-8", "strict": True},
        headers=auth_headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body == {
        "decoded": "Hallo wereld",
        "input_length": 16,
        "output_bytes": 12,
        "encoding": "utf-8",
        "detected_alphabet": "standard",
    }


def test_decode_tolerant_voor_whitespace(client, auth_headers):
    r = client.post(
        "/decode",
        json={"data": "SGFsbG8g\nd2Vy ZWxk"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["decoded"] == "Hallo wereld"
    assert body["input_length"] == 16


def test_decode_ongeldig_teken_400(client, auth_headers):
    r = client.post(
        "/decode",
        json={"data": "SGVsbG8=!!"},
        headers=auth_headers,
    )
    assert r.status_code == 400
    body = r.json()
    assert body["error_code"] == "INVALID_BASE64_CHARACTER"
    assert body["position"] == 8
    assert "'!'" in body["message"]


def test_decode_verkeerde_padding_400(client, auth_headers):
    r = client.post(
        "/decode",
        json={"data": "SGVsbG8"},
        headers=auth_headers,
    )
    assert r.status_code == 400
    body = r.json()
    assert body["error_code"] == "INVALID_PADDING"
    assert "deelbaar door 4" in body["message"]


def test_decode_niet_utf8_400(client, auth_headers):
    r = client.post(
        "/decode",
        json={"data": "/w==", "strict": True},
        headers=auth_headers,
    )
    assert r.status_code == 400
    body = r.json()
    assert body["error_code"] == "NOT_DECODABLE_TEXT"
    assert body["position"] == 0


def test_decode_url_safe_detected_alphabet(client, auth_headers):
    r = client.post(
        "/decode",
        json={"data": "fn5-fn4_"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["decoded"] == "~~~~~?"
    assert body["detected_alphabet"] == "url_safe"


def test_decode_zonder_data_veld_422(client, auth_headers):
    r = client.post(
        "/decode",
        json={},
        headers=auth_headers,
    )
    assert r.status_code == 422
    body = r.json()
    assert body["error_code"] == "MISSING_FIELD"
    assert "data" in body["message"]


def test_validate_geldige_base64(client, auth_headers):
    r = client.post(
        "/validate",
        json={"data": "SGFsbG8gd2VyZWxk"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["valid"] is True
    assert body["error_code"] is None
    assert body["position"] is None
    assert body["detected_alphabet"] == "standard"


def test_validate_ongeldige_base64_blijft_200(client, auth_headers):
    r = client.post(
        "/validate",
        json={"data": "SGFsbG8gd2VyZWxk!!"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["valid"] is False
    assert body["error_code"] == "INVALID_BASE64_CHARACTER"
    assert body["position"] == 16
    assert "'!'" in body["message"]


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
    r = client.get("/status", headers=auth_headers)
    body = r.json()
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
    for endpoint, payload in gevallen:
        r = client.post(endpoint, json=payload, headers=auth_headers)
        assert r.status_code >= 400
        body = r.json()
        keys = set(body.keys())
        assert keys == {"error_code", "message", "detail", "position"}
        assert isinstance(body["error_code"], str) and body["error_code"]
        assert isinstance(body["message"], str) and body["message"]
        assert body["detail"] is None or isinstance(body["detail"], str)
        assert body["position"] is None or isinstance(body["position"], int)


def test_verkeerd_content_type_422(client, auth_headers):
    headers = dict(auth_headers)
    headers["Content-Type"] = "text/plain"
    r = client.post("/encode", content="dit is geen json", headers=headers)
    assert r.status_code == 422
    body = r.json()
    assert body["error_code"] == "INVALID_CONTENT_TYPE"
    assert "application/json" in body["message"]


def test_niet_json_body_422(client, auth_headers):
    headers = dict(auth_headers)
    headers["Content-Type"] = "application/json"
    r = client.post("/encode", content="{ongeldig json", headers=headers)
    assert r.status_code == 422
    body = r.json()
    assert body["error_code"] == "INVALID_JSON"
    assert isinstance(body["detail"], str)


def test_json_body_geen_object_422(client, auth_headers):
    headers = dict(auth_headers)
    headers["Content-Type"] = "application/json"
    r = client.post("/decode", content='"alleen een string"', headers=headers)
    assert r.status_code == 422
    body = r.json()
    assert body["error_code"] == "INVALID_JSON"


def test_roundtrip_property_via_http(client, auth_headers):
    random.seed(7)
    pool = "abcXYZ019 ~?!+/-_\n\téàß☕日"
    teksten = ["Hallo wereld", "café ☕", "~~~~~?"]
    for _ in range(15):
        lengte = random.randint(1, 30)
        teksten.append("".join(random.choice(pool) for __ in range(lengte)))
    for tekst in teksten:
        r1 = client.post("/encode", json={"text": tekst}, headers=auth_headers)
        assert r1.status_code == 200
        encoded = r1.json()["encoded"]
        r2 = client.post("/decode", json={"data": encoded}, headers=auth_headers)
        assert r2.status_code == 200
        decoded = r2.json()["decoded"]
        assert decoded == tekst
