import pytest
from src.errors import Base64Error
from src.logic import (
    decode_data,
    detect_alphabet,
    encode_text,
    normalize_padding,
    service_status,
    validate_characters,
    validate_data,
)


def test_encode_text_hallo_wereld():
    result = encode_text("Hallo wereld")
    assert result == {
        "input_text": "Hallo wereld",
        "encoded": "SGFsbG8gd2VyZWxk",
        "alphabet": "standard",
        "input_bytes": 12,
        "output_length": 16,
    }


def test_encode_text_url_safe_uses_dash_and_underscore():
    standard = encode_text("\U0001F600ÿÿ")
    assert standard["encoded"] == "8J+YgMO/w78="
    urlsafe = encode_text("\U0001F600ÿÿ", url_safe=True)
    assert urlsafe["encoded"] == "8J-YgMO_w78="
    assert "+" not in urlsafe["encoded"] and "/" not in urlsafe["encoded"]
    assert urlsafe["alphabet"] == "url_safe" and standard["alphabet"] == "standard"
    assert urlsafe["input_bytes"] == 8


def test_encode_text_strip_padding():
    result = encode_text("Hallo", strip_padding=True)
    assert result["encoded"] == "SGFsbG8"
    assert "=" not in result["encoded"]
    assert result["output_length"] == 7
    assert result["input_bytes"] == 5


def test_encode_text_empty_raises_empty_input():
    with pytest.raises(Base64Error) as excinfo:
        encode_text("")
    assert excinfo.value.error_code == "EMPTY_INPUT"
    assert "'text'" in excinfo.value.message
    assert excinfo.value.detail != ""


def test_detect_alphabet_variants():
    assert detect_alphabet("SGFsbG8gd2VyZWxk") == "standard"
    assert detect_alphabet("w7/Dvw==") == "standard"
    assert detect_alphabet("8J-YgMO_w78=") == "url_safe"
    assert detect_alphabet("SGFsbG8=", url_safe=True) == "url_safe"


def test_validate_characters_invalid_character_reports_position():
    with pytest.raises(Base64Error) as excinfo:
        validate_characters("SGFsbG8g@d2VyZWxk", "standard")
    assert excinfo.value.error_code == "INVALID_BASE64_CHARACTER"
    assert excinfo.value.message == "Ongeldig teken '@' op positie 8 voor base64 alfabet"


def test_validate_characters_allows_padding_and_valid_chars():
    assert validate_characters("SGFsbG8=", "standard") is None
    assert validate_characters("8J-YgMO_w78=", "url_safe") is None


def test_validate_characters_urlsafe_rejects_plus():
    with pytest.raises(Base64Error) as excinfo:
        validate_characters("8J+YgMO_w78=", "url_safe")
    assert excinfo.value.error_code == "INVALID_BASE64_CHARACTER"
    assert "positie 2" in excinfo.value.message


def test_normalize_padding_correct_padding_unchanged():
    assert normalize_padding("SGFsbG8=", True) == ("SGFsbG8=", False)
    assert normalize_padding("SGFsbG8gd2VyZWxk", False) == ("SGFsbG8gd2VyZWxk", False)


def test_normalize_padding_fixes_missing_padding():
    assert normalize_padding("SGFsbG8", True) == ("SGFsbG8=", True)


def test_normalize_padding_missing_padding_without_fix_raises():
    with pytest.raises(Base64Error) as excinfo:
        normalize_padding("SGFsbG8", False)
    assert excinfo.value.error_code == "INVALID_PADDING"
    assert "fix_padding" in excinfo.value.message


def test_normalize_padding_remainder_one_always_invalid():
    with pytest.raises(Base64Error) as excinfo:
        normalize_padding("SGFsb", True)
    assert excinfo.value.error_code == "INVALID_PADDING"
    assert "rest van 1" in excinfo.value.message


def test_normalize_padding_equals_inside_string_raises():
    with pytest.raises(Base64Error) as excinfo:
        normalize_padding("SG=sbG8g", True)
    assert excinfo.value.error_code == "INVALID_PADDING"
    assert "positie 2" in excinfo.value.message


def test_normalize_padding_too_many_padding_chars_raises():
    with pytest.raises(Base64Error) as excinfo:
        normalize_padding("SGFs====", True)
    assert excinfo.value.error_code == "INVALID_PADDING"
    assert "Te veel padding" in excinfo.value.message


def test_decode_data_standard():
    result = decode_data("SGFsbG8gd2VyZWxk")
    assert result == {
        "input_data": "SGFsbG8gd2VyZWxk",
        "decoded": "Hallo wereld",
        "alphabet": "standard",
        "padding_fixed": False,
        "output_length": 12,
    }


def test_decode_data_detects_url_safe():
    result = decode_data("8J-YgMO_w78=")
    assert result["alphabet"] == "url_safe"
    assert result["decoded"] == "\U0001F600ÿÿ"
    assert result["output_length"] == 3
    assert result["padding_fixed"] is False


def test_decode_data_invalid_character_raises():
    with pytest.raises(Base64Error) as excinfo:
        decode_data("SGFsbG8g@d2VyZWxk")
    assert excinfo.value.error_code == "INVALID_BASE64_CHARACTER"
    assert "positie 8" in excinfo.value.message


def test_decode_data_padding_fixed():
    result = decode_data("SGFsbG8", fix_padding=True)
    assert result["decoded"] == "Hallo"
    assert result["padding_fixed"] is True
    assert result["output_length"] == 5


def test_decode_data_padding_error_without_fix():
    with pytest.raises(Base64Error) as excinfo:
        decode_data("SGFsbG8", fix_padding=False)
    assert excinfo.value.error_code == "INVALID_PADDING"


def test_decode_data_not_utf8_raises():
    with pytest.raises(Base64Error) as excinfo:
        decode_data("//4=")
    assert excinfo.value.error_code == "NOT_UTF8_DECODABLE"
    assert "UTF-8" in excinfo.value.message


def test_decode_data_empty_raises():
    with pytest.raises(Base64Error) as excinfo:
        decode_data("")
    assert excinfo.value.error_code == "EMPTY_INPUT"
    assert "'data'" in excinfo.value.message


def test_round_trip_encode_decode_all_flag_combinations():
    texts = ["Hallo wereld", "héllo €", "\U0001F600ÿÿ", "regel1\nregel2\n", "a"]
    for text in texts:
        for url_safe in (False, True):
            for strip_padding in (False, True):
                encoded = encode_text(text, url_safe=url_safe, strip_padding=strip_padding)["encoded"]
                result = decode_data(encoded, url_safe=url_safe, fix_padding=True)
                assert result["decoded"] == text
                assert result["alphabet"] == ("url_safe" if url_safe else "standard")


def test_validate_data_valid():
    assert validate_data("SGFsbG8gd2VyZWxk") == {
        "data": "SGFsbG8gd2VyZWxk",
        "valid": True,
        "reason": None,
        "error_code": None,
    }


def test_validate_data_invalid_character():
    result = validate_data("SGFsbG8g@d2VyZWxk")
    assert result["valid"] is False
    assert result["error_code"] == "INVALID_BASE64_CHARACTER"
    assert result["reason"] == "Ongeldig teken '@' op positie 8 voor base64 alfabet"
    assert result["data"] == "SGFsbG8g@d2VyZWxk"


def test_validate_data_empty():
    result = validate_data("")
    assert result["valid"] is False
    assert result["error_code"] == "EMPTY_INPUT"


def test_validate_data_padding_problem():
    result = validate_data("SGFsbG8")
    assert result["valid"] is False
    assert result["error_code"] == "INVALID_PADDING"


def test_validate_data_ignores_utf8_problems():
    result = validate_data("//4=")
    assert result["valid"] is True
    assert result["error_code"] is None


def test_service_status():
    result = service_status()
    assert result["status"] == "ok"
    assert result["service"] == "base64_service"
    assert result["supported_alphabets"] == ["standard", "url_safe"]
    assert isinstance(result["version"], str) and result["version"] != ""
