from app.fetcher import fetch_url
from app.parser import parse_html


def main():
    result = fetch_url("https://example.com")
    print(result["success"], result["status_code"], result["error"])

    if result["success"]:
        parsed = parse_html(result["url"], result["html"])
        print("Title:", parsed["title"])
        print("Link count:", len(parsed["links"]))
        print("First links:", parsed["links"][:5])


if __name__ == "__main__":
    main()