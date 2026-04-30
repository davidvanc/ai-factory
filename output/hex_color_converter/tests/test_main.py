from click.testing import CliRunner
from src.main import main

def test_cli_valid_hex():
    runner = CliRunner()
    result = runner.invoke(main, ['#FF5733'])
    assert result.exit_code == 0
    assert 'Hex: #FF5733' in result.output
    assert 'RGB: (255, 87, 51)' in result.output
    assert 'HSL: (11, 100, 60)' in result.output

def test_cli_valid_hex_without_hash():
    runner = CliRunner()
    result = runner.invoke(main, ['FF5733'])
    assert result.exit_code == 0
    assert 'Hex: #FF5733' in result.output
    assert 'RGB: (255, 87, 51)' in result.output
    assert 'HSL: (11, 100, 60)' in result.output

def test_cli_short_hex():
    runner = CliRunner()
    result = runner.invoke(main, ['#FFF'])
    assert result.exit_code == 0
    assert 'Hex: #FFF' in result.output
    assert 'RGB: (255, 255, 255)' in result.output
    assert 'HSL: (0, 0, 100)' in result.output

def test_cli_invalid_hex():
    runner = CliRunner()
    result = runner.invoke(main, ['GGGGGG'])
    assert result.exit_code == 0
    assert 'Error:' in result.output

def test_cli_missing_argument():
    runner = CliRunner()
    result = runner.invoke(main, [])
    assert result.exit_code != 0
    assert 'Error' in result.output or 'Missing argument' in result.output
