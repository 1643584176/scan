from __future__ import annotations

import re
from html.parser import HTMLParser
from urllib.parse import urlsplit

from assettrace.models import (
    AssetSnapshot,
    DetectorResult,
    Discovery,
    FindingDraft,
)
from assettrace.urls import InvalidUrl, canonicalize_url


class _SurfaceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.scripts: list[str] = []
        self.links: list[str] = []
        self.forms: list[dict[str, str]] = []
        self.current_form: dict[str, str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): value or "" for key, value in attrs}
        tag = tag.lower()
        if tag == "script" and values.get("src"):
            self.scripts.append(values["src"])
        elif tag == "a" and values.get("href"):
            self.links.append(values["href"])
        elif tag == "form":
            self.current_form = {
                "action": values.get("action", ""),
                "method": values.get("method", "get").lower(),
                "method_explicit": str("method" in values).lower(),
                "has_password": "false",
            }
            self.forms.append(self.current_form)
        elif tag == "input" and self.current_form is not None:
            if values.get("type", "").lower() == "password":
                self.current_form["has_password"] = "true"

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "form":
            self.current_form = None


class HtmlSurfaceDetector:
    key = "html-surface"
    version = "1.2.0"
    supported_kinds = frozenset({"page"})

    def analyze(self, snapshot: AssetSnapshot) -> DetectorResult:
        parser = _SurfaceParser()
        parser.feed(snapshot.text)
        base_url = snapshot.final_url or snapshot.url
        discoveries: list[Discovery] = []
        findings: list[FindingDraft] = []

        for raw_url in parser.scripts:
            resolved = self._resolve(raw_url, base_url)
            if not resolved:
                continue
            discoveries.append(
                Discovery(
                    url=resolved,
                    kind="javascript",
                    relation="loads-script",
                    fetch=True,
                )
            )
            if snapshot.url.startswith("https://") and resolved.startswith("http://"):
                findings.append(
                    FindingDraft(
                        dedupe_key=f"mixed-script:{urlsplit(resolved).path}",
                        title="Page loads JavaScript over HTTP",
                        category="mixed-content",
                        severity="high",
                        confidence="high",
                        evidence=f"Insecure script URL: {resolved}",
                        remediation="Serve the script over HTTPS and update the page reference.",
                        location=resolved,
                    )
                )

        for raw_url in parser.links:
            resolved = self._resolve(raw_url, base_url)
            if resolved:
                discoveries.append(
                    Discovery(
                        url=resolved,
                        kind="endpoint",
                        relation="links-to",
                    )
                )

        for index, form in enumerate(parser.forms, start=1):
            action = self._resolve(form["action"] or base_url, base_url)
            if action:
                discoveries.append(
                    Discovery(
                        url=action,
                        kind="endpoint",
                        relation="submits-to",
                    )
                )
            if (
                form["has_password"] == "true"
                and form["method"] == "get"
                and form["method_explicit"] == "true"
            ):
                findings.append(
                    FindingDraft(
                        dedupe_key=f"password-form-get:{index}",
                        title="Password form submits with GET",
                        category="sensitive-data-exposure",
                        severity="high",
                        confidence="high",
                        evidence=f"Form #{index} contains a password input and uses GET.",
                        remediation="Submit credentials with POST over HTTPS and prevent URL logging.",
                        location=action or snapshot.url,
                    )
                )
            if (
                form["has_password"] == "true"
                and action
                and action.startswith("http://")
            ):
                findings.append(
                    FindingDraft(
                        dedupe_key=f"password-form-http:{index}",
                        title="Password form submits over HTTP",
                        category="transport-security",
                        severity="critical",
                        confidence="high",
                        evidence=f"Form #{index} submits credentials to {action}.",
                        remediation="Submit credentials only to an HTTPS endpoint.",
                        location=action,
                    )
                )

        stack_pattern = _stack_trace_pattern()
        if stack_pattern.search(snapshot.text):
            findings.append(
                FindingDraft(
                    dedupe_key="error-stack-trace-exposed",
                    title="Page appears to expose an application stack trace",
                    category="error-disclosure",
                    severity="medium",
                    confidence="medium",
                    evidence=(
                        "The HTML response contains text patterns that look like "
                        "a server or application stack trace."
                    ),
                    remediation=(
                        "Return a generic error page to clients and keep stack traces "
                        "only in protected server-side logs."
                    ),
                    location=snapshot.url,
                )
            )

        return DetectorResult(
            findings=findings,
            discoveries=_dedupe_discoveries(discoveries),
            facts={
                "external_scripts": len(parser.scripts),
                "forms": len(parser.forms),
                "links": len(parser.links),
            },
        )

    @staticmethod
    def _resolve(raw_url: str, base_url: str) -> str | None:
        if raw_url.strip().lower().startswith(
            ("javascript:", "data:", "mailto:", "tel:", "#")
        ):
            return None
        try:
            return canonicalize_url(raw_url, base_url)
        except (InvalidUrl, ValueError):
            return None


def _dedupe_discoveries(items: list[Discovery]) -> list[Discovery]:
    unique: dict[tuple[str, str, str], Discovery] = {}
    for item in items:
        unique[(item.url, item.kind, item.relation)] = item
    return list(unique.values())


def _stack_trace_pattern() -> re.Pattern[str]:
    return re.compile(
        (
            r"Traceback \(most recent call last\):"
            r"|Exception in thread"
            r"|Stack trace:"
            r"|System\.[A-Za-z0-9_.]+Exception"
            r"|at [A-Za-z0-9_.$<>]+\([A-Za-z0-9_.$<>]+\.java:\d+\)"
        ),
        re.IGNORECASE,
    )
