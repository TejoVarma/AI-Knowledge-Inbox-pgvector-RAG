import socket

import httpx
import pytest

from app.services import url_fetcher
from app.services.url_fetcher import UrlFetchError, fetch_url_text

PUBLIC_IP = "93.184.216.34"
PAGE = "<html><body><p>Hello from a public page</p></body></html>"


@pytest.fixture()
def dns(monkeypatch):
    """Fake DNS: map hostnames to the addresses we want, never touch the network."""
    table: dict[str, list[str]] = {}

    def fake_getaddrinfo(host, port, *args, **kwargs):
        addresses = table.get(host, [host])  # literal ips resolve to themselves
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (a, port)) for a in addresses]

    monkeypatch.setattr(url_fetcher.socket, "getaddrinfo", fake_getaddrinfo)
    return table


@pytest.fixture()
def web(monkeypatch):
    """Fake web server: tests register handlers by Host header; every request is recorded."""
    routes: dict[str, httpx.Response] = {}
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return routes[f"{request.headers['host']}{request.url.path}"]

    monkeypatch.setattr(
        url_fetcher, "_client", lambda: httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=False)
    )
    return routes, seen


def html(body: str = PAGE, content_type: str = "text/html; charset=utf-8") -> httpx.Response:
    return httpx.Response(200, headers={"content-type": content_type}, text=body)


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/",
        "http://10.0.0.5/",
        "http://192.168.1.1/",
        "http://169.254.169.254/latest/meta-data/",  # cloud metadata service
        "http://0.0.0.0/",
        "http://[::1]/",
        "http://[::ffff:127.0.0.1]/",  # ipv4 loopback disguised as ipv6
    ],
)
def test_internal_addresses_are_refused(dns, url):
    with pytest.raises(UrlFetchError, match="private or internal"):
        fetch_url_text(url)


@pytest.mark.parametrize(
    "url, reason",
    [
        ("ftp://example.com/file", "only http and https"),
        ("file:///etc/passwd", "only http and https"),
        ("http://user:secret@example.com/", "credentials"),
        ("http://example.com:8080/", "standard web ports"),
        ("http://example.com:22/", "standard web ports"),
    ],
)
def test_unsafe_url_shapes_are_refused(dns, url, reason):
    with pytest.raises(UrlFetchError, match=reason):
        fetch_url_text(url)


def test_hostname_that_resolves_to_a_private_address_is_refused(dns):
    dns["intranet.example"] = ["10.1.2.3"]
    with pytest.raises(UrlFetchError, match="private or internal"):
        fetch_url_text("https://intranet.example/")


def test_one_private_address_among_public_ones_is_enough_to_refuse(dns):
    dns["mixed.example"] = [PUBLIC_IP, "127.0.0.1"]
    with pytest.raises(UrlFetchError, match="private or internal"):
        fetch_url_text("https://mixed.example/")


def test_public_page_is_fetched_from_the_checked_address(dns, web):
    routes, seen = web
    dns["news.example"] = [PUBLIC_IP]
    routes["news.example/story"] = html()

    assert fetch_url_text("https://news.example/story") == "Hello from a public page"
    # connected to the ip we checked, while still saying which site we want
    assert seen[0].url.host == PUBLIC_IP
    assert seen[0].headers["host"] == "news.example"


def test_redirect_to_an_internal_address_is_refused(dns, web):
    routes, seen = web
    dns["short.example"] = [PUBLIC_IP]
    routes["short.example/go"] = httpx.Response(302, headers={"location": "http://169.254.169.254/latest/meta-data/"})

    with pytest.raises(UrlFetchError, match="private or internal"):
        fetch_url_text("https://short.example/go")
    assert len(seen) == 1  # never made the second request


def test_redirect_to_a_public_page_is_followed(dns, web):
    routes, _ = web
    dns["short.example"] = [PUBLIC_IP]
    routes["short.example/go"] = httpx.Response(301, headers={"location": "/article"})
    routes["short.example/article"] = html()

    assert fetch_url_text("https://short.example/go") == "Hello from a public page"


def test_redirect_loops_are_cut_off(dns, web):
    routes, seen = web
    dns["loop.example"] = [PUBLIC_IP]
    routes["loop.example/a"] = httpx.Response(302, headers={"location": "/a"})

    with pytest.raises(UrlFetchError, match="too many redirects"):
        fetch_url_text("https://loop.example/a")
    assert len(seen) == url_fetcher.MAX_REDIRECTS + 1


def test_oversized_pages_are_refused(dns, web):
    routes, _ = web
    dns["big.example"] = [PUBLIC_IP]
    routes["big.example/"] = html("x" * (url_fetcher.MAX_DOWNLOAD_BYTES + 1))

    with pytest.raises(UrlFetchError, match="too large"):
        fetch_url_text("https://big.example/")


def test_non_text_content_is_refused(dns, web):
    routes, _ = web
    dns["img.example"] = [PUBLIC_IP]
    routes["img.example/cat.png"] = html("not really a png", content_type="image/png")

    with pytest.raises(UrlFetchError, match="unsupported content type"):
        fetch_url_text("https://img.example/cat.png")
