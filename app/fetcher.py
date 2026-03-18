from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


DEFAULT_TIMEOUT = 5


def fetch_url(url: str, timeout: int = DEFAULT_TIMEOUT) -> dict:
    request = Request(
        url,
        headers={
            "User-Agent": "LocalCrawler/1.0"
        },
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            status_code = getattr(response, "status", 200)
            content_type = response.headers.get("Content-Type", "")
            charset = response.headers.get_content_charset() or "utf-8"

            if "text/html" not in content_type.lower():
                return {
                    "success": False,
                    "url": url,
                    "status_code": status_code,
                    "error": f"Unsupported content type: {content_type}",
                    "content_type": content_type,
                    "html": "",
                }

            raw_bytes = response.read()
            html = raw_bytes.decode(charset, errors="replace")

            return {
                "success": True,
                "url": url,
                "status_code": status_code,
                "error": None,
                "content_type": content_type,
                "html": html,
            }

    except HTTPError as e:
        return {
            "success": False,
            "url": url,
            "status_code": e.code,
            "error": f"HTTPError: {e.reason}",
            "content_type": "",
            "html": "",
        }
    except URLError as e:
        return {
            "success": False,
            "url": url,
            "status_code": None,
            "error": f"URLError: {e.reason}",
            "content_type": "",
            "html": "",
        }
    except Exception as e:
        return {
            "success": False,
            "url": url,
            "status_code": None,
            "error": f"Unexpected error: {str(e)}",
            "content_type": "",
            "html": "",
        }