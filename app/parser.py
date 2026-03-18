from html.parser import HTMLParser
from collections import Counter

from app.utils import normalize_url, tokenize


class LinkAndTextParser(HTMLParser):
    def __init__(self, base_url: str):
        super().__init__()
        self.base_url = base_url
        self.links = set()
        self.text_parts = []
        self.in_title = False
        self.title_parts = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            href = dict(attrs).get("href")
            normalized = normalize_url(self.base_url, href) if href else None
            if normalized:
                self.links.add(normalized)

        if tag.lower() == "title":
            self.in_title = True

    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data):
        stripped = data.strip()
        if not stripped:
            return

        self.text_parts.append(stripped)
        if self.in_title:
            self.title_parts.append(stripped)

    def get_result(self):
        title = " ".join(self.title_parts).strip()
        body_text = " ".join(self.text_parts).strip()
        return {
            "title": title,
            "body_text": body_text,
            "links": sorted(self.links),
        }


def parse_html(base_url: str, html: str) -> dict:
    parser = LinkAndTextParser(base_url)
    parser.feed(html)
    return parser.get_result()


def term_frequencies(text: str) -> list[tuple[str, int]]:
    counts = Counter(tokenize(text))
    return sorted(counts.items())