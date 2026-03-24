from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import ssl


DEFAULT_TIMEOUT = 10


def fetch_url(url: str, timeout: int = DEFAULT_TIMEOUT) -> dict:
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; LocalCrawler/1.0)",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )

    ssl_context = ssl.create_default_context()

    try:
        with urlopen(request, timeout=timeout, context=ssl_context) as response:
            status_code = getattr(response, "status", 200)
            final_url = response.geturl()
            content_type = response.headers.get("Content-Type", "")
            charset = response.headers.get_content_charset() or "utf-8"

            if "text/html" not in content_type.lower():
                return {
                    "success": False,
                    "url": final_url,
                    "status_code": status_code,
                    "error": f"Unsupported content type: {content_type}",
                    "content_type": content_type,
                    "html": "",
                }

            raw_bytes = response.read()
            html = raw_bytes.decode(charset, errors="replace")

            return {
                "success": True,
                "url": final_url,
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
    except ssl.SSLError as e:
        return {
            "success": False,
            "url": url,
            "status_code": None,
            "error": f"SSLError: {str(e)}",
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