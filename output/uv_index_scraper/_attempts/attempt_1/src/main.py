from src.scraper import fetch_uv_index
from src.advisor import get_advice

def main():
    uv_index = fetch_uv_index()
    advice = get_advice(uv_index)
    print(advice)

if __name__ == "__main__":
    main()