import click
from src.json_reader import read_json
from src.stats import calculate_sum, calculate_average, calculate_max

@click.command()
@click.argument('filepath', type=click.Path(exists=False))
def main(filepath):
    """Lees een JSON bestand met een lijst getallen en toon som, gemiddelde en maximum."""
    try:
        numbers = read_json(filepath)
        total = calculate_sum(numbers)
        avg = calculate_average(numbers)
        max_val = calculate_max(numbers)
        click.echo(f"Som: {total}")
        click.echo(f"Gemiddelde: {avg}")
        click.echo(f"Maximum: {max_val}")
    except FileNotFoundError as e:
        click.echo(f"Fout: {e}", err=True)
        raise SystemExit(1)
    except ValueError as e:
        click.echo(f"Fout: {e}", err=True)
        raise SystemExit(1)

if __name__ == '__main__':
    main()
