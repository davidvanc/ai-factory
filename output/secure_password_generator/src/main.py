import argparse
import sys
from src.generator import generate_password

def main():
    parser = argparse.ArgumentParser(description='Generate a secure random password.')
    parser.add_argument('--length', type=int, default=16, help='Length of the password (default: 16)')
    parser.add_argument('--no-special', action='store_true', help='Exclude special characters from the password')
    args = parser.parse_args()

    if args.length < 1:
        print('Error: length must be at least 1', file=sys.stderr)
        sys.exit(1)

    password = generate_password(length=args.length, use_special=not args.no_special)
    print(password)

if __name__ == '__main__':
    main()
