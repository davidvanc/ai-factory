import json
import pytest
from pydantic import ValidationError
from src import errors
from src.errors import ApiError
from src.logic import reset_state
from src.models import EncodeRequest, EncodeResponse

@pytest.fixture(autouse=True)
def _reset_state():
    reset_state()
    yield
    reset_state()

def test_api_error_to_dict_bevat_altijd_vier_keys():
    exc = ApiError(400, "X_CODE", "boodschap")
    assert exc.to_dict() == {"error_code": "X_CODE", "message": "boodschap", "detail": None, "position": None}

def test_api_error_to_response_status_en_body():
    exc = ApiError(400, "X_CODE", "boodschap", detail="uitleg", position=3)
    resp = exc.to_response()
    assert resp.status_code == 400
    body = json.loads(resp.body)
    assert body == {"error_code": "X_CODE", "message": "boodschap", "detail": "uitleg", "position": 3}

def test_error_response_functie_gelijk_aan_to_response():
    exc = ApiError(422, errors.EMPTY_INPUT, "leeg")
    resp = errors.error_response(exc)
    assert resp.status_code == 422
    assert json.loads(resp.body)["error_code"] == "EMPTY_INPUT"

def test_empty_input_helper():
    exc = errors.empty_input("text")
    assert exc.status_code == 422 and exc.error_code == "EMPTY_INPUT"
    assert "text" in exc.message

def test_missing_field_helper():
    exc = errors.missing_field("data")
    assert exc.status_code == 422 and exc.error_code == "MISSING_FIELD"
    assert "data" in exc.message and exc.position is None

def test_input_too_large_helper():
    exc = errors.input_too_large(200, 100)
    assert exc.status_code == 413 and exc.error_code == "INPUT_TOO_LARGE"
    assert "200" in exc.message and "100" in exc.message

def test_invalid_json_helper():
    exc = errors.invalid_json("Expecting value: line 1 column 1")
    assert exc.status_code == 422 and exc.error_code == "INVALID_JSON"
    assert exc.detail == "Expecting value: line 1 column 1"

def test_invalid_content_type_helper():
    exc = errors.invalid_content_type("text/plain")
    assert exc.status_code == 422 and exc.error_code == "INVALID_CONTENT_TYPE"
    assert "text/plain" in exc.detail

def test_unsupported_encoding_helper():
    exc = errors.unsupported_encoding("klingon", ["utf-8", "ascii"])
    assert exc.status_code == 422 and exc.error_code == "UNSUPPORTED_ENCODING"
    assert "klingon" in exc.message and "utf-8" in exc.detail

def test_from_pydantic_error_missing_veld():
    with pytest.raises(ValidationError) as info:
        EncodeResponse.model_validate({})
    exc = errors.from_pydantic_error(info.value)
    assert exc.status_code == 422 and exc.error_code == "MISSING_FIELD"
    assert "encoded" in exc.message
    assert isinstance(exc.detail, str) and "encoded" in exc.detail

def test_from_pydantic_error_verkeerd_type():
    with pytest.raises(ValidationError) as info:
        EncodeRequest.model_validate({"text": 5})
    exc = errors.from_pydantic_error(info.value)
    assert exc.status_code == 422 and exc.error_code == "VALIDATION_ERROR"
    assert "text" in exc.message

def test_from_pydantic_error_extra_veld_verboden():
    with pytest.raises(ValidationError) as info:
        EncodeRequest.model_validate({"text": "a", "onbekend": 1})
    exc = errors.from_pydantic_error(info.value)
    assert exc.status_code == 422 and exc.error_code == "VALIDATION_ERROR"
    assert "onbekend" in exc.message
