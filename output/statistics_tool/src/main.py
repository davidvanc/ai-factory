import argparse
import sys
from src.statistics_calculator import calculate_statistics

def main():
    parser = argparse.ArgumentParser(description='Bereken statistieken van een lijst getallen.')
    parser.add_argument('numbers', nargs='+', type=float, help='Lijst van getallen')
    args = parser.parse_args()

    try:
        stats = calculate_statistics(args.numbers)
        print(f"Gemiddelde: {stats['mean']}")
        print(f"Mediaan: {stats['median']}")
        print(f"Standaarddeviatie: {stats['std']}")
    except (ValueError, TypeError) as e:
        print(f"Fout: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
