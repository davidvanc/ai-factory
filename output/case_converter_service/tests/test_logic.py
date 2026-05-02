import pytest
from src.logic import (
    get_words, to_upper, to_lower, to_title, 
    to_snake, to_kebab, to_camel, convert_case
)

def test_get_words():
    assert get_words("hello world") == ["hello", "world"]
    assert get_words("hello_world") == ["hello", "world"]
    assert get_words("hello-world") == ["hello", "world"]
    assert get_words("helloWorld") == ["hello", "World"]

def test_logic_functions_special_chars_and_empty():
    # Empty strings
    assert get_words("") == []
    assert to_upper("") == ""
    assert to_camel("") == ""
    assert to_snake("") == ""
    
    # Special characters
    assert get_words("!@#$%^&*()") == []
    assert to_upper("!@#$%^&*()") == ""
    assert to_snake("hello!@#world") == "hello_world"
    assert to_camel("   multiple   spaces  ! ") == "multipleSpaces"

def test_convert_case_valid():
    assert convert_case("test string", "upper") == "TEST STRING"
    assert convert_case("TEST STRING", "lower") == "test string"
    assert convert_case("test string", "title") == "Test String"
    assert convert_case("test string", "snake") == "test_string"
    assert convert_case("test string", "kebab") == "test-string"
    assert convert_case("test string", "camel") == "testString"

def test_convert_case_invalid():
    with pytest.raises(ValueError):
        convert_case("test string", "unknown_case")
