import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit

import httpx
from bs4 import BeautifulSoup

USER_AGENT = "AIKnowledgeInbox/1.0"
MAX_CONTENT_CHARS = 50_000
MAX_DOWNLOAD_BYTES = 2_000_000
MAX_REDIRECTS = 5
ALLOWED_PORTS = {80, 443}
ALLOWED_CONTENT_TYPES = ("text/html", "text/plain", "application/xhtml+xml")


class UrlFetchError(Exception):
    pass


def fetch_url_text(url: str) -> str:
    html = _download(url)

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()

    text = " ".join(soup.get_text(separator=" ").split())
    if not text:
        raise UrlFetchError("no readable text content found at url")

    return text[:MAX_CONTENT_CHARS]


def _download(url: str) -> str:
    # redirects are followed by hand so every hop gets the same checks - otherwise a
    # public page could simply redirect us to an internal address
    with _client() as client:
        for _ in range(MAX_REDIRECTS + 1):
            target = _check_url(url)
            try:
                with client.stream(
                    "GET",
                    target.pinned_url,
                    headers={"User-Agent": USER_AGENT, "Host": target.hostname},
                    extensions={"sni_hostname": target.hostname},
                ) as response:
                    if response.is_redirect:
                        location = response.headers.get("location")
                        if not location:
                            raise UrlFetchError("redirect without a location")
                        url = urljoin(url, location)
                        continue
                    response.raise_for_status()
                    return _read_limited(response)
            except httpx.HTTPError as exc:
                raise UrlFetchError(f"failed to fetch url: {exc}") from exc
    raise UrlFetchError("too many redirects")


def _client() -> httpx.Client:
    return httpx.Client(timeout=10.0, follow_redirects=False)


def _read_limited(response: httpx.Response) -> str:
    content_type = response.headers.get("content-type", "").split(";")[0].strip().lower()
    if content_type and content_type not in ALLOWED_CONTENT_TYPES:
        raise UrlFetchError(f"unsupported content type: {content_type}")

    body = bytearray()
    for chunk in response.iter_bytes():
        body.extend(chunk)
        if len(body) > MAX_DOWNLOAD_BYTES:
            raise UrlFetchError("page is too large")
    return body.decode(response.encoding or "utf-8", errors="replace")


@dataclass
class _CheckedTarget:
    hostname: str
    pinned_url: str


def _check_url(url: str) -> _CheckedTarget:
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https"):
        raise UrlFetchError("only http and https urls are allowed")
    if parts.username or parts.password:
        raise UrlFetchError("urls with credentials are not allowed")
    if not parts.hostname:
        raise UrlFetchError("url has no host")

    try:
        port = parts.port or (443 if parts.scheme == "https" else 80)
    except ValueError as exc:
        raise UrlFetchError("invalid port") from exc
    if port not in ALLOWED_PORTS:
        raise UrlFetchError("only the standard web ports (80, 443) are allowed")

    ip = _resolve_public_ip(parts.hostname, port)

    # connect to the exact address we just checked, so a second dns lookup can't hand
    # back a different (internal) one - "dns rebinding". tls still verifies the real
    # hostname through sni
    host_for_url = f"[{ip}]" if ip.version == 6 else str(ip)
    pinned = parts._replace(netloc=f"{host_for_url}:{port}").geturl()
    return _CheckedTarget(parts.hostname, pinned)


def _resolve_public_ip(hostname: str, port: int) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
    try:
        infos = socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise UrlFetchError("could not resolve the url's host") from exc

    addresses = [ipaddress.ip_address(info[4][0]) for info in infos]
    if not addresses:
        raise UrlFetchError("could not resolve the url's host")

    # every address must be public: if any is internal, a later lookup could pick that one
    for address in addresses:
        if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped:
            address = address.ipv4_mapped
        if not address.is_global:
            raise UrlFetchError("url points to a private or internal address")
    return addresses[0]
