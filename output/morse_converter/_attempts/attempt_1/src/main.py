# src/main.py
import click
from src.morse import text_to_morse, morse_to_text

@click.group()
def cli():
    """Morse code converter."""
    pass

@cli.command()
@click.argument('text', type=str)
def encode(text: str):
    """Convert plain text to Morse code."""
    result = text_to_morse(text)
    click.echo(result)

@cli.command()
@click.argument('morse', type=str)
def decode(morse: str):
    """Convert Morse code back to plain text."""
    result = morse_to_text(morse)
    click.echo(result)

if __name__ == '__main__':
    cli()
