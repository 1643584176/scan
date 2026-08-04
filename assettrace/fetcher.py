from __future__ import annotations

import asyncio
import ipaddress
import socket
from urllib.parse import urljoin

import httpx

from assettrace.config import Settings
from assettrace.models import FetchResult
from assettrace.urls import canonicalize_url


PERSISTED_RESPONSE_HEADERS = frozenset(
    {
        "access-control-allow-credentials",
        "access-control-allow-headers",
        "access-control-allow-methods",
        "access-control-allow-origin",
        "cache-control",
        "content-length",
        "content-security-policy",
        "content-type",
        "cross-origin-embedder-policy",
        "cross-origin-opener-policy",
        "cross-origin-resource-policy",
        "etag",
        "expires",
        "last-modified",
        "permissions-policy",
        "pragma",
        "referrer-policy",
        "server",
        "set-cookie",
        "strict-transport-security",
        "vary",
        "x-content-type-options",
        "x-frame-options",
        "x-powered-by",
    }
)


class FetchBlocked(RuntimeError):
    pass


class ResponseTooLarge(RuntimeError):
    pass


class HttpFetcher:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def fetch(
        self,
        url: str,
        previous_revision: dict | None = None,
    ) -> FetchResult:
        current_url = canonicalize_url(url)
        redirect_chain: list[str] = []
        conditional_headers: dict[str, str] = {}
        if previous_revision:
            previous_headers = previous_revision.get("headers_json", {})
            if previous_headers.get("etag"):
                conditional_headers["If-None-Match"] = previous_headers["etag"]
            if previous_headers.get("last-modified"):
                conditional_headers["If-Modified-Since"] = previous_headers[
                    "last-modified"
                ]

        async with httpx.AsyncClient(
            timeout=self.settings.request_timeout_seconds,
            follow_redirects=False,
            trust_env=False,
            headers={
                "User-Agent": self.settings.user_agent,
                "Accept": "text/html,application/javascript,text/javascript,*/*;q=0.5",
            },
        ) as client:
            for redirect_number in range(6):
                await self._validate_target(current_url)
                request_headers = conditional_headers if redirect_number == 0 else {}
                async with client.stream(
                    "GET", current_url, headers=request_headers
                ) as response:
                    persisted_headers = self._persisted_headers(response.headers)
                    if response.status_code == 304 and previous_revision:
                        return FetchResult(
                            requested_url=canonicalize_url(url),
                            final_url=previous_revision["final_url"],
                            status_code=previous_revision["status_code"],
                            headers=previous_revision["headers_json"],
                            body=b"",
                            not_modified=True,
                            redirect_chain=tuple(redirect_chain),
                        )
                    if response.is_redirect:
                        location = response.headers.get("location")
                        if not location:
                            raise FetchBlocked("Redirect response has no Location header")
                        redirect_chain.append(current_url)
                        current_url = canonicalize_url(urljoin(current_url, location))
                        continue

                    declared_length = response.headers.get("content-length")
                    if declared_length and declared_length.isdigit():
                        if int(declared_length) > self.settings.max_body_bytes:
                            raise ResponseTooLarge(
                                f"Response declares {declared_length} bytes; "
                                f"limit is {self.settings.max_body_bytes}"
                            )

                    chunks: list[bytes] = []
                    received = 0
                    async for chunk in response.aiter_bytes():
                        received += len(chunk)
                        if received > self.settings.max_body_bytes:
                            raise ResponseTooLarge(
                                f"Response exceeded {self.settings.max_body_bytes} bytes"
                            )
                        chunks.append(chunk)
                    return FetchResult(
                        requested_url=canonicalize_url(url),
                        final_url=current_url,
                        status_code=response.status_code,
                        headers=persisted_headers,
                        body=b"".join(chunks),
                        redirect_chain=tuple(redirect_chain),
                    )

        raise FetchBlocked("Too many redirects")

    async def _validate_target(self, url: str) -> None:
        if self.settings.allow_private_targets:
            return
        host = httpx.URL(url).host
        if not host:
            raise FetchBlocked("Target has no hostname")

        loop = asyncio.get_running_loop()
        try:
            addresses = await loop.getaddrinfo(
                host,
                None,
                family=socket.AF_UNSPEC,
                type=socket.SOCK_STREAM,
            )
        except socket.gaierror as exc:
            raise FetchBlocked(f"DNS lookup failed for {host}") from exc

        if not addresses:
            raise FetchBlocked(f"DNS lookup returned no addresses for {host}")
        for address in addresses:
            ip = ipaddress.ip_address(address[4][0])
            if (
                ip.is_private
                or ip.is_loopback
                or ip.is_link_local
                or ip.is_multicast
                or ip.is_reserved
                or ip.is_unspecified
            ):
                raise FetchBlocked(f"Target resolves to blocked address {ip}")

    @staticmethod
    def _persisted_headers(headers: httpx.Headers) -> dict[str, str]:
        return {
            key.lower(): value
            for key, value in headers.items()
            if key.lower() in PERSISTED_RESPONSE_HEADERS
        }
