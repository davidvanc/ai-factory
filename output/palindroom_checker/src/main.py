import click
from src.palindrome import is_palindrome


@click.command()
@click.argument('text')
def main(text: str):
    """Check if the given word or phrase is a palindrome."""
    if is_palindrome(text):
        click.echo("Yes, it's a palindrome!")
    else:
        click.echo("No, it's not a palindrome.")


if __name__ == '__main__':
    main()
