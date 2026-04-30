import click
from src.converter import hex_to_rgb, hex_to_hsl
from src.validator import validate_hex

@click.command()
@click.argument('hex_color', required=True)
def main(hex_color):
    """Convert a hex color code to RGB and HSL values."""
    try:
        hex_color = validate_hex(hex_color)
    except ValueError as e:
        click.echo(f"Error: {e}")
        return

    rgb = hex_to_rgb(hex_color)
    hsl = hex_to_hsl(hex_color)

    click.echo(f"Hex: #{hex_color}")
    click.echo(f"RGB: {rgb}")
    click.echo(f"HSL: {hsl}")

if __name__ == '__main__':
    main()
