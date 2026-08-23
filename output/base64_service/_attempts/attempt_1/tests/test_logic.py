import json
import pytest
from fastapi.responses import JSONResponse
from src.errors import (
    Base64DecodeFailedError,
    Base64ServiceError,
    InputTooLargeError,
    InvalidBase64CharacterError,
    InvalidBase64LengthError,
    NonUtf8PayloadError,
)
from src.logic import (
    check_input_size,
    compute_padding,
    decode_data,
    encode_text,
    validate_base64_characters,
)
from src.models import MAX_INPUT_BYTES

ROUNDTRIP_TEXTS = [
    "",
    "a",
    "Hallo wereld",
    "caf\u00e9 \u2713",
    "\U0001F389 feest \U0001F680",
    "\u00c6r\u00f8sk\u00f8bing",
    "regel1\nregel2\ttab",
    "0123456789+/=",
    "\u00ff\u00ff\u00fe",
]

def test_check_input_size_binnen_limiet_geeft_none() -> None:
    assert check_input_size(0, 10) is None
    assert check_input_size(10, 10) is None
    assert check_input_size(MAX_INPUT_BYTES) is None

def test_check_input_size_boven_limiet_gooit_input_too_large() -> None:
    with pytest.raises(InputTooLargeError) as excinfo:
        check_input_size(11, 10)
    exc = excinfo.value
    assert exc.size == 11 and exc.limit == 10
    assert exc.status_code == 413
    assert exc.error == "input_too_large"
    assert "maximum" in exc.message and "10" in exc.message
    assert "10" in exc.detail

def test_check_input_size_gebruikt_default_limiet() -> None:
    with pytest.raises(InputTooLargeError) as excinfo:
        check_input_size(MAX_INPUT_BYTES + 1)
    assert excinfo.value.limit == MAX_INPUT_BYTES
    assert excinfo.value.size == MAX_INPUT_BYTES + 1

def test_validate_base64_characters_geldige_invoer_geeft_none() -> None:
    assert validate_base64_characters("", False) is None
    assert validate_base64_characters("SGFsbG8gd2VyZWxk", False) is None
    assert validate_base64_characters("SGFsbG8=", False) is None
    assert validate_base64_characters("w7_Dv8O-", True) is None

def test_validate_base64_characters_dollar_teken_positie_3() -> None:
    with pytest.raises(InvalidBase64CharacterError) as excinfo:
        validate_base64_characters("abc$$$", False)
    exc = excinfo.value
    assert exc.character == "$" and exc.position == 3 and exc.url_safe is False
    assert exc.status_code == 422 and exc.error == "invalid_base64_character"
    assert "ongeldige base64" in exc.message
    assert "3" in exc.message
    assert "'+', '/'" in exc.detail

def test_validate_base64_characters_urlsafe_tekens_ongeldig_in_standaard() -> None:
    with pytest.raises(InvalidBase64CharacterError) as excinfo:
        validate_base64_characters("ab-_", False)
    assert excinfo.value.character == "-" and excinfo.value.position == 2
    assert "'+', '/'" in excinfo.value.detail

def test_validate_base64_characters_standaardtekens_ongeldig_in_urlsafe() -> None:
    with pytest.raises(InvalidBase64CharacterError) as excinfo:
        validate_base64_characters("ab+/", True)
    exc = excinfo.value
    assert exc.character == "+" and exc.position == 2 and exc.url_safe is True
    assert "'-', '_'" in exc.detail

def test_validate_base64_characters_whitespace_is_ongeldig() -> None:
    with pytest.raises(InvalidBase64CharacterError) as excinfo:
        validate_base64_characters("SGFs bG8=", False)
    assert excinfo.value.character == " " and excinfo.value.position == 4

def test_compute_padding_geldige_lengtes() -> None:
    assert compute_padding("") == 0
    assert compute_padding("SGFsbG8gd2VyZWxk") == 0
    assert compute_padding("SGFsbG8=") == 0
    assert compute_padding("YQ") == 2
    assert compute_padding("SGFsbG8") == 1

def test_compute_padding_lengte_modulo_vier_is_een_gooit_fout() -> None:
    with pytest.raises(InvalidBase64LengthError) as excinfo:
        compute_padding("SGFsbG8gd2VyZWxka")
    exc = excinfo.value
    assert exc.length == 17
    assert exc.status_code == 422 and exc.error == "invalid_base64_length"
    assert "ongeldige base64" in exc.message and "17" in exc.message
    assert "deelbaar is door 4" in exc.detail
    with pytest.raises(InvalidBase64LengthError) as excinfo2:
        compute_padding("A")
    assert excinfo2.value.length == 1

def test_encode_text_standaard() -> None:
    assert encode_text("Hallo wereld") == ("SGFsbG8gd2VyZWxk", False)
    assert encode_text("") == ("", False)
    assert encode_text("caf\u00e9 \u2713") == ("Y2Fmw6kg4pyT", False)

def test_encode_text_url_safe_gebruikt_dash_en_underscore() -> None:
    standaard, _ = encode_text("\u00ff\u00ff\u00fe")
    urlsafe, _ = encode_text("\u00ff\u00ff\u00fe", url_safe=True)
    assert standaard == "w7/Dv8O+"
    assert urlsafe == "w7_Dv8O-"
    assert "+" in standaard and "/" in standaard
    assert "-" in urlsafe and "_" in urlsafe
    assert "+" not in urlsafe and "/" not in urlsafe
    assert urlsafe == standaard.replace("+", "-").replace("/", "_")

def test_encode_text_strip_padding() -> None:
    assert encode_text("a") == ("YQ==", False)
    assert encode_text("a", strip_padding=True) == ("YQ", True)
    assert encode_text("Hallo", strip_padding=True) == ("SGFsbG8", True)
    assert encode_text("Hallo wereld", strip_padding=True) == ("SGFsbG8gd2VyZWxk", False)

def test_encode_text_te_grote_invoer_gooit_input_too_large() -> None:
    with pytest.raises(InputTooLargeError) as excinfo:
        encode_text("\u00e9" * 5, limit=9)
    assert excinfo.value.size == 10 and excinfo.value.limit == 9
    assert excinfo.value.status_code == 413

def test_decode_data_standaard() -> None:
    assert decode_data("SGFsbG8gd2VyZWxk") == ("Hallo wereld", 0)
    assert decode_data("") == ("", 0)
    assert decode_data("Y2Fmw6kg4pyT") == ("caf\u00e9 \u2713", 0)

def test_decode_data_vult_padding_aan() -> None:
    assert decode_data("YQ") == ("a", 2)
    assert decode_data("SGFsbG8") == ("Hallo", 1)
    assert decode_data("YQ==") == ("a", 0)

def test_decode_data_url_safe() -> None:
    assert decode_data("w7_Dv8O-", url_safe=True) == ("\u00ff\u00ff\u00fe", 0)
    with pytest.raises(InvalidBase64CharacterError) as excinfo:
        decode_data("w7/Dv8O+", url_safe=True)
    assert excinfo.value.character == "/" and excinfo.value.position == 2 and excinfo.value.url_safe is True

def test_decode_data_ongeldig_teken() -> None:
    with pytest.raises(InvalidBase64CharacterError) as excinfo:
        decode_data("abc$$$")
    assert excinfo.value.character == "$" and excinfo.value.position == 3
    assert "ongeldige base64" in excinfo.value.message

def test_decode_data_ongeldige_lengte() -> None:
    with pytest.raises(InvalidBase64LengthError) as excinfo:
        decode_data("SGFsbG8gd2VyZWxka")
    assert excinfo.value.length == 17 and excinfo.value.status_code == 422

def test_decode_data_niet_utf8_payload() -> None:
    with pytest.raises(NonUtf8PayloadError) as excinfo:
        decode_data("//8=")
    exc = excinfo.value
    assert exc.status_code == 422 and exc.error == "non_utf8_payload"
    assert exc.position == 0
    assert isinstance(exc.reason, str) and exc.reason != ""
    assert "UTF-8" in exc.message and "niet-tekstuele" in exc.message
    assert "byte-positie 0" in exc.detail

def test_decode_data_decoder_faalt_alsnog() -> None:
    with pytest.raises(Base64DecodeFailedError) as excinfo:
        decode_data("SG=s")
    exc = excinfo.value
    assert exc.status_code == 422 and exc.error == "invalid_base64"
    assert "ongeldige base64" in exc.message
    assert isinstance(exc.reason, str) and exc.reason != ""

def test_decode_data_te_grote_invoer_gooit_input_too_large() -> None:
    with pytest.raises(InputTooLargeError) as excinfo:
        decode_data("A" * 8, limit=4)
    assert excinfo.value.size == 8 and excinfo.value.limit == 4 and excinfo.value.status_code == 413

@pytest.mark.parametrize("text", ROUNDTRIP_TEXTS)
def test_roundtrip_standaard(text: str) -> None:
    encoded, padding_stripped = encode_text(text)
    assert padding_stripped is False
    decoded, padding_added = decode_data(encoded)
    assert decoded == text
    assert padding_added == 0

@pytest.mark.parametrize("text", ROUNDTRIP_TEXTS)
def test_roundtrip_url_safe_zonder_padding(text: str) -> None:
    encoded, _ = encode_text(text, url_safe=True, strip_padding=True)
    assert "=" not in encoded
    decoded, padding_added = decode_data(encoded, url_safe=True)
    assert decoded == text
    assert padding_added in (0, 1, 2)

def test_base64_service_error_to_payload_vorm() -> None:
    err = Base64ServiceError("x_error", "kort bericht", "lange uitleg", 400)
    payload = err.to_payload()
    assert list(payload.keys()) == ["error", "message", "detail"]
    assert payload == {"error": "x_error", "message": "kort bericht", "detail": "lange uitleg"}
    assert err.status_code == 400
    assert str(err) == "kort bericht"

def test_base64_service_error_to_response() -> None:
    err = InputTooLargeError(2048, 1024)
    response = err.to_response()
    assert isinstance(response, JSONResponse)
    assert response.status_code == 413
    body = json.loads(response.body)
    assert body == {"error": err.error, "message": err.message, "detail": err.detail}
    assert set(body.keys()) == {"error", "message", "detail"}
