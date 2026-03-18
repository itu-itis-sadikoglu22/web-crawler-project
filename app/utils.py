import re
from urllib.parse import urljoin, urlparse, urlunparse


def normalize_url(base_url: str, raw_url: str) -> str | None:
    if not raw_url:
        return None

    absolute = urljoin(base_url, raw_url)
    parsed = urlparse(absolute)

    if parsed.scheme not in ("http", "https"):
        return None

    if not parsed.netloc:
        return None

    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()

    if scheme == "http" and netloc.endswith(":80"):
        netloc = netloc[:-3]
    if scheme == "https" and netloc.endswith(":443"):
        netloc = netloc[:-4]

    path = parsed.path or "/"
    if path != "/" and path.endswith("/"):
        path = path[:-1]

    normalized = urlunparse((scheme, netloc, path, "", parsed.query, ""))
    return normalized


def tokenize(text: str) -> list[str]:
    if not text:
        return []

    tokens = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return [token for token in tokens if len(token) > 1]