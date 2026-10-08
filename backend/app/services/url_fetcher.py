import httpx
from bs4 import BeautifulSoup

USER_AGENT = "AIKnowledgeInbox/1.0"
MAX_CONTENT_CHARS = 50_000


class UrlFetchError(Exception):
    pass


def fetch_url_text(url: str) -> str:
    try:
        response = httpx.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=10.0,
            follow_redirects=True,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise UrlFetchError(f"failed to fetch url: {exc}") from exc

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()

    text = " ".join(soup.get_text(separator=" ").split())
    if not text:
        raise UrlFetchError("no readable text content found at url")

    return text[:MAX_CONTENT_CHARS]
