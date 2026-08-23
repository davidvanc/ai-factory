import random
import pytest
from src import config
from src import logic
from src.errors import ApiError

@pytest.fixture(autouse=True)
def _reset_state():
    logic.reset_state()
    yield
    logic.reset_state()

def test_strip_whitespace_verwijdert_en_mapt_indices():
    cleaned, index_map = logic.strip_whitespace("SGFs\nbG8=")
    assert cleaned == "SGFsbG8="
    assert index_map == [0, 1, 2, 3, 5, 6, 7, 8]

def test_normalize_encoding_aliassen():
    assert logic.normalize_encoding("UTF8") == "utf-8"
    assert logic.normalize_encoding(" utf-8 ") == "utf-8"
    assert logic.normalize_encoding("ISO-8859-1") == "latin-1"

def test_normalize_encoding_onbekend_gooit_apierror():
    with pytest.raises(ApiError) as info:
        logic.normalize_encoding("klingon")
    assert info.value.status_code == 422 and info.value.error_code == "UNSUPPORTED_ENCODING"

def test_encode_text_basis():
    res = logic.encode_text("Hallo wereld", False, "utf-8")
    assert res.encoded == "SGFsbG8gd2VyZWxk"
    assert res.input_bytes == 12 and res.output_length == 16
    assert res.url_safe is False and res.encoding == "utf-8"

def test_encode_text_url_safe_alfabet():
    std = logic.encode_text("~~~~~?", False, "utf-8")
    url = logic.encode_text("~~~~~?", True, "utf-8")
    assert std.encoded == "fn5+fn4/"
    assert url.encoded == "fn5-fn4_"
    assert "+" not in url.encoded and "/" not in url.encoded

def test_encode_text_unicode():
    res = logic.encode_text("café ☕", False, "utf-8")
    assert res.encoded == "Y2Fmw6kg4piV"
    assert res.input_bytes == 9 and res.output_length == 12

def test_encode_text_leeg_gooit_empty_input():
    with pytest.raises(ApiError) as info:
        logic.encode_text("", False, "utf-8")
    assert info.value.status_code == 422 and info.value.error_code == "EMPTY_INPUT"
    assert "text" in info.value.message

def test_encode_text_te_groot_gooit_413():
    groot = "a" * (config.MAX_INPUT_BYTES + 1)
    with pytest.raises(ApiError) as info:
        logic.encode_text(groot, False, "utf-8")
    assert info.value.status_code == 413 and info.value.error_code == "INPUT_TOO_LARGE"

def test_encode_text_niet_encodeerbaar():
    with pytest.raises(ApiError) as info:
        logic.encode_text("café", False, "ascii")
    assert info.value.status_code == 422 and info.value.error_code == "NOT_ENCODABLE_TEXT"
    assert info.value.position == 3

def test_check_base64_geldig_standard():
    check = logic.check_base64("SGFsbG8gd2VyZWxk")
    assert check.valid is True and check.alphabet == "standard"
    assert check.cleaned == "SGFsbG8gd2VyZWxk" and check.error_code is None

def test_check_base64_geldig_url_safe():
    check = logic.check_base64("fn5-fn4_")
    assert check.valid is True and check.alphabet == "url_safe"

def test_check_base64_whitespace_tolerant():
    check = logic.check_base64("SGFsbG8g\n d2VyZWxk")
    assert check.valid is True and check.cleaned == "SGFsbG8gd2VyZWxk"

def test_check_base64_leeg():
    check = logic.check_base64("   \n ")
    assert check.valid is False and check.error_code == "EMPTY_INPUT" and check.position is None

def test_check_base64_ongeldig_teken_positie():
    check = logic.check_base64("SGFsbG8gd2VyZWxk!!")
    assert check.valid is False and check.error_code == "INVALID_BASE64_CHARACTER"
    assert check.position == 16 and "'!'" in check.message and "16" in check.message

def test_check_base64_ongeldig_teken_positie_na_whitespace():
    check = logic.check_base64("SGFs\nbG8!")
    assert check.valid is False and check.error_code == "INVALID_BASE64_CHARACTER"
    assert check.position == 8

def test_check_base64_lengte_niet_deelbaar_door_vier():
    check = logic.check_base64("SGVsbG8")
    assert check.valid is False and check.error_code == "INVALID_PADDING"
    assert "deelbaar door 4" in check.message and check.position is None

def test_check_base64_padding_in_midden():
    check = logic.check_base64("SG=sbG8=")
    assert check.valid is False and check.error_code == "INVALID_PADDING"
    assert check.position == 3 and "einde" in check.message

def test_check_base64_te_veel_padding():
    check = logic.check_base64("SGVsbA=====")
    assert check.valid is False and check.error_code == "INVALID_PADDING"
    assert check.position == 8 and "Te veel padding" in check.message

def test_check_base64_gemengd_alfabet():
    check = logic.check_base64("ab-c+d==")
    assert check.valid is False and check.error_code == "MIXED_ALPHABET"
    assert check.position == 4

def test_decode_base64_to_text_basis():
    res = logic.decode_base64_to_text("SGFsbG8gd2VyZWxk", "utf-8", True)
    assert res.decoded == "Hallo wereld"
    assert res.input_length == 16 and res.output_bytes == 12
    assert res.encoding == "utf-8" and res.detected_alphabet == "standard"

def test_decode_base64_to_text_whitespace():
    res = logic.decode_base64_to_text("SGFsbG8g\nd2Vy ZWxk", "utf-8", True)
    assert res.decoded == "Hallo wereld" and res.input_length == 16

def test_decode_base64_to_text_url_safe():
    res = logic.decode_base64_to_text("fn5-fn4_", "utf-8", True)
    assert res.decoded == "~~~~~?" and res.detected_alphabet == "url_safe"
    assert res.output_bytes == 6 and res.input_length == 8

def test_decode_ongeldig_teken_gooit_400():
    with pytest.raises(ApiError) as info:
        logic.decode_base64_to_text("SGVsbG8=!!", "utf-8", True)
    assert info.value.status_code == 400
    assert info.value.error_code == "INVALID_BASE64_CHARACTER" and info.value.position == 8

def test_decode_verkeerde_padding_gooit_400():
    with pytest.raises(ApiError) as info:
        logic.decode_base64_to_text("SGVsbG8", "utf-8", True)
    assert info.value.status_code == 400 and info.value.error_code == "INVALID_PADDING"
    assert "deelbaar door 4" in info.value.message

def test_decode_niet_utf8_gooit_400():
    with pytest.raises(ApiError) as info:
        logic.decode_base64_to_text("/w==", "utf-8", True)
    assert info.value.status_code == 400 and info.value.error_code == "NOT_DECODABLE_TEXT"
    assert info.value.position == 0

def test_decode_niet_utf8_non_strict_vervangt():
    res = logic.decode_base64_to_text("/w==", "utf-8", False)
    assert res.decoded == "\ufffd" and res.output_bytes == 1

def test_decode_leeg_gooit_422():
    with pytest.raises(ApiError) as info:
        logic.decode_base64_to_text("  ", "utf-8", True)
    assert info.value.status_code == 422 and info.value.error_code == "EMPTY_INPUT"

def test_decode_te_groot_gooit_413():
    with pytest.raises(ApiError) as info:
        logic.decode_base64_to_text("A" * (config.MAX_INPUT_BYTES + 1), "utf-8", True)
    assert info.value.status_code == 413 and info.value.error_code == "INPUT_TOO_LARGE"

def test_decode_onbekende_encoding_gooit_422():
    with pytest.raises(ApiError) as info:
        logic.decode_base64_to_text("SGVsbG8=", "klingon", True)
    assert info.value.status_code == 422 and info.value.error_code == "UNSUPPORTED_ENCODING"

def test_validate_base64_string_geldig():
    res = logic.validate_base64_string("SGFsbG8gd2VyZWxk")
    assert res.valid is True and res.error_code is None and res.position is None

def test_validate_base64_string_ongeldig():
    res = logic.validate_base64_string("SGFsbG8gd2VyZWxk!!")
    assert res.valid is False and res.error_code == "INVALID_BASE64_CHARACTER"
    assert res.position == 16 and "'!'" in res.message

def test_validate_base64_string_te_groot_geeft_geen_exception():
    res = logic.validate_base64_string("A" * (config.MAX_INPUT_BYTES + 1))
    assert res.valid is False and res.error_code == "INPUT_TOO_LARGE"

def test_counters_en_reset_state():
    logic.encode_text("a", False, "utf-8")
    logic.encode_text("b", False, "utf-8")
    logic.decode_base64_to_text("SGVsbG8=", "utf-8", True)
    logic.validate_base64_string("SGVsbG8=")
    assert logic.get_counters() == {"encode": 2, "decode": 1, "validate": 1, "total": 4}
    logic.reset_state()
    assert logic.get_counters() == {"encode": 0, "decode": 0, "validate": 0, "total": 0}

def test_roundtrip_deterministische_teksten():
    teksten = ["a", "Hallo wereld", "café ☕", "~~~~~?", "日本語テキスト", "regel1\nregel2\ttab", "!@#$%^&*()_+-=", "x" * 1000]
    for tekst in teksten:
        for url_safe in (False, True):
            enc = logic.encode_text(tekst, url_safe, "utf-8")
            dec = logic.decode_base64_to_text(enc.encoded, "utf-8", True)
            assert dec.decoded == tekst

def test_roundtrip_willekeurige_teksten():
    random.seed(20240501)
    pool = "abcXYZ019 ~?!+/-_\n\téàß☕日"
    for _ in range(25):
        lengte = random.randint(1, 40)
        tekst = "".join(random.choice(pool) for _ in range(lengte))
        enc = logic.encode_text(tekst, False, "utf-8")
        assert logic.decode_base64_to_text(enc.encoded, "utf-8", True).decoded == tekst
