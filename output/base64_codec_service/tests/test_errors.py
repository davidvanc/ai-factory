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
    err = ApiError(400, "X_CODE", "boodschap")
    d = err.to_dict()
    assert d == {"error_code": "X_CODE", "message": "boodschap", "detail": None, "position": None}

def test_api_error_to_response_status_en_body():
    err = ApiError(400, "X_CODE", "boodschap", detail="uitleg", position=3)
    resp = err.to_response()
    assert resp.status_code == 400
    body = json.loads(resp.body)
    assert body == {"error_code": "X_CODE", "message": "boodschap", "detail": "uitleg", "position": 3}

def test_error_response_functie_gelijk_aan_to_response():
    err = ApiError(422, errors.EMPTY_INPUT, "leeg")
    resp = errors.error_response(err)
    assert resp.status_code == 422
    body = json.loads(resp.body)
    assert body["error_code"] == "EMPTY_INPUT"

def test_empty_input_helper():
    err = errors.empty_input("text")
    assert err.status_code == 422
    assert err.error_code == errors.EMPTY_INPUT
    assert "text" in err.message
    assert err.position is None

def test_missing_field_helper():
    err = errors.missing_field("data")
    assert err.status_code == 422
    assert err.error_code == errors.MISSING_FIELD
    assert "data" in err.message
    assert err.position is None

def test_input_too_large_helper():
    err = errors.input_too_large(200, 100)
    assert err.status_code == 413
    assert err.error_code == errors.INPUT_TOO_LARGE
    assert "200" in err.message
    assert "100" in err.message

def test_invalid_json_helper():
    err = errors.invalid_json("Expecting value: line 1 column 1")
    assert err.status_code == 422
    assert err.error_code == errors.INVALID_JSON
    assert err.detail == "Expecting value: line 1 column 1"

def test_invalid_content_type_helper():
    err = errors.invalid_content_type("text/plain")
    assert err.status_code == 422
    assert err.error_code == errors.INVALID_CONTENT_TYPE
    assert "text/plain" in err.detail

def test_unsupported_encoding_helper():
    err = errors.unsupported_encoding("klingon", ["utf-8", "ascii"])
    assert err.status_code == 422
    assert err.error_code == errors.UNSUPPORTED_ENCODING
    assert "klingon" in err.message
    assert "utf-8" in err.detail

def test_from_pydantic_error_missing_veld():
    with pytest.raises(ValidationError) as info:
        EncodeResponse.model_validate({})
    err = errors.from_pydantic_error(info.value)
    assert err.status_code == 422
    assert err.error_code == errors.MISSING_FIELD
    assert "encoded" in err.message
    assert isinstance(err.detail, str)
    assert "encoded" in err.detail

def test_from_pydantic_error_verkeerd_type():
    with pytest.raises(ValidationError) as info:
        EncodeRequest.model_validate({"text": 5})
    err = errors.from_pydantic_error(info.value)
    assert err.status_code == 422
    assert err.error_code == errors.VALIDATION_ERROR
    assert "text" in err.message

def test_from_pydantic_error_extra_veld_verboden():
    with pytest.raises(ValidationError) as info:
        EncodeRequest.model_validate({"text": "a", "onbekend": 1})
    err = errors.from_pydantic_error(info.value)
    assert err.status_code == 422
    assert err.error_code == errors.VALIDATION_ERROR
    assert "onbekend" in err.message
