import pytest
from click.testing import CliRunner
from src.palindrome import is_palindrome
from src.main import main


def test_palindroom_woord():
    assert is_palindrome("lepel") == True


def test_niet_palindroom():
    assert is_palindrome("python") == False


def test_palindroom_zin():
    zin = "Een ree, maak niet zo'n lawaai, met Fredje naast mij nabij ja dat is waar, zei Piet met hevige pret die waarde laadde, leek rede tot een teweeggaand peurende druk"
    assert is_palindrome(zin) == True


def test_hoofdletters():
    assert is_palindrome("Lepel") == True
    assert is_palindrome("LEPEL") == True


def test_lege_string():
    assert is_palindrome("") == True


def test_cli_output():
    runner = CliRunner()
    result = runner.invoke(main, ["lepel"])
    assert result.exit_code == 0
    assert "Yes, it's a palindrome!" in result.output

    result2 = runner.invoke(main, ["python"])
    assert result2.exit_code == 0
    assert "No, it's not a palindrome." in result2.output
