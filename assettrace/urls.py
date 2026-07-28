from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit


class InvalidUrl(ValueError):
    pass


def canonicalize_url(raw_url: str, base_url: str | None = None) -> str:
    value = raw_url.strip()
    if base_url:
        value = urljoin(base_url, value)
    if "://" not in value:
        value = f"https://{value}"

    parsed = urlsplit(value)
    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https"}:
        raise InvalidUrl("Only HTTP and HTTPS URLs are supported")
    if not parsed.hostname:
        raise InvalidUrl("URL must include a hostname")
    if parsed.username or parsed.password:
        raise InvalidUrl("Credentials in URLs are not supported")

    host = parsed.hostname.encode("idna").decode("ascii").lower()
    port = parsed.port
    if port and not (
        (scheme == "http" and port == 80) or (scheme == "https" and port == 443)
    ):
        netloc = f"{host}:{port}"
    else:
        netloc = host

    path = parsed.path or "/"
    query = urlencode(sorted(parse_qsl(parsed.query, keep_blank_values=True)), doseq=True)
    return urlunsplit((scheme, netloc, path, query, ""))


def hostname(url: str) -> str:
    return (urlsplit(url).hostname or "").lower()


def is_same_host(left: str, right: str) -> bool:
    return hostname(left) == hostname(right)


def is_host_in_scope(url: str, scope_host: str) -> bool:
    target_host = hostname(url)
    normalized_scope = scope_host.strip(".").lower()
    return target_host == normalized_scope or target_host.endswith(
        f".{normalized_scope}"
    )
