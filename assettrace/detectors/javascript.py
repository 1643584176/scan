from __future__ import annotations

import re
from urllib.parse import urlsplit

from assettrace.models import (
    AssetSnapshot,
    DetectorResult,
    Discovery,
    FindingDraft,
)
from assettrace.urls import InvalidUrl, canonicalize_url


SECRET_PATTERNS = (
    (
        "aws-access-key",
        re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
        "Possible AWS access key in JavaScript",
    ),
    (
        "github-token",
        re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,255}\b"),
        "Possible GitHub token in JavaScript",
    ),
    (
        "stripe-live-secret",
        re.compile(r"\bsk_live_[A-Za-z0-9]{20,}\b"),
        "Possible Stripe live secret in JavaScript",
    ),
    (
        "private-key",
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
        "Private key material in JavaScript",
    ),
)

ENDPOINT_PATTERN = re.compile(
    r"""(?P<quote>["'`])(?P<url>(?:https?://[^"'`\s]+|/[\w./?=&%:-]{2,}))(?P=quote)"""
)

SOURCE_PATTERNS = (
    "location.search",
    "location.hash",
    "document.url",
    "document.referrer",
    "window.name",
    "message.data",
)
SINK_PATTERNS = (
    "innerhtml",
    "outerhtml",
    "insertadjacenthtml",
    "document.write",
    "eval(",
    "settimeout(",
    "setinterval(",
)


class JavaScriptDetector:
    key = "javascript-static"
    version = "1.4.0"
    supported_kinds = frozenset({"javascript"})

    def analyze(self, snapshot: AssetSnapshot) -> DetectorResult:
        text = snapshot.text
        lowered = text.lower()
        findings: list[FindingDraft] = []
        discoveries: list[Discovery] = []

        for secret_type, pattern, title in SECRET_PATTERNS:
            for match_index, match in enumerate(pattern.finditer(text), start=1):
                findings.append(
                    FindingDraft(
                        dedupe_key=f"{secret_type}:{match_index}",
                        title=title,
                        category="secret-exposure",
                        severity="critical",
                        confidence="high",
                        evidence=f"Matched {secret_type}: {_redact(match.group(0))}",
                        remediation="Revoke the credential, remove it from client code, and rotate it.",
                        location=snapshot.url,
                    )
                )

        for match in ENDPOINT_PATTERN.finditer(text):
            raw_url = match.group("url")
            try:
                resolved = canonicalize_url(raw_url, snapshot.final_url or snapshot.url)
            except (InvalidUrl, ValueError):
                continue
            endpoint_host = (urlsplit(resolved).hostname or "").lower()
            if _looks_internal_or_development_hostname(endpoint_host):
                findings.append(
                    FindingDraft(
                        dedupe_key=f"internal-endpoint-host:{endpoint_host}",
                        title="JavaScript references an internal or development host",
                        category="asset-exposure",
                        severity="low",
                        confidence="high",
                        evidence=(
                            "A public JavaScript string references the "
                            f"internal/development-looking host {endpoint_host}."
                        ),
                        remediation=(
                            "Remove unused environment endpoints from production "
                            "bundles and keep internal service names out of public "
                            "client-side code."
                        ),
                        location=snapshot.url,
                    )
                )
            discoveries.append(
                Discovery(
                    url=resolved,
                    kind="endpoint",
                    relation="references-endpoint",
                )
            )

        source_hits = sorted(item for item in SOURCE_PATTERNS if item in lowered)
        sink_hits = sorted(item for item in SINK_PATTERNS if item in lowered)
        if source_hits and sink_hits:
            findings.append(
                FindingDraft(
                    dedupe_key="dom-xss-source-sink",
                    title="JavaScript contains DOM input sources and execution sinks",
                    category="dom-xss-review",
                    severity="info",
                    confidence="low",
                    evidence=(
                        f"Sources: {', '.join(source_hits)}; "
                        f"sinks: {', '.join(sink_hits)}. No data flow was proven."
                    ),
                    remediation="Trace whether attacker-controlled values reach the listed sinks.",
                    location=snapshot.url,
                )
            )

        source_map = re.search(
            r"(?://[#@]\s*sourceMappingURL=)([^\s;]+)", text
        )
        if source_map:
            try:
                map_url = canonicalize_url(
                    source_map.group(1), snapshot.final_url or snapshot.url
                )
            except (InvalidUrl, ValueError):
                map_url = ""
            if map_url:
                discoveries.append(
                    Discovery(
                        url=map_url,
                        kind="source-map",
                        relation="references-source-map",
                        fetch=True,
                    )
                )
                findings.append(
                    FindingDraft(
                        dedupe_key="public-source-map-reference",
                        title="JavaScript exposes a source map reference",
                        category="source-map-exposure",
                        severity="info",
                        confidence="high",
                        evidence=f"The asset publishes sourceMappingURL to {map_url}.",
                        remediation=(
                            "Remove production sourceMappingURL comments or "
                            "serve source maps only through an intended controlled path."
                        ),
                        location=snapshot.url,
                    )
                )
                map_host = (urlsplit(map_url).hostname or "").lower()
                if _looks_internal_or_development_hostname(map_host):
                    findings.append(
                        FindingDraft(
                            dedupe_key=f"internal-source-map-host:{map_host}",
                            title="JavaScript references an internal source map host",
                            category="source-map-exposure",
                            severity="low",
                            confidence="high",
                            evidence=(
                                "A public JavaScript sourceMappingURL points to "
                                f"the internal-looking host {map_host}."
                            ),
                            remediation=(
                                "Remove production sourceMappingURL comments or "
                                "publish source maps only through an intended "
                                "public endpoint with access control."
                            ),
                            location=snapshot.url,
                        )
                    )

        return DetectorResult(
            findings=findings,
            discoveries=_dedupe_discoveries(discoveries),
            facts={
                "endpoint_references": len(discoveries),
                "source_indicators": source_hits,
                "sink_indicators": sink_hits,
            },
        )


def _redact(value: str) -> str:
    if len(value) <= 8:
        return "[redacted]"
    return f"{value[:4]}...{value[-4:]}"


def _dedupe_discoveries(items: list[Discovery]) -> list[Discovery]:
    unique: dict[tuple[str, str, str], Discovery] = {}
    for item in items:
        unique[(item.url, item.kind, item.relation)] = item
    return list(unique.values())


def _looks_internal_or_development_hostname(hostname: str) -> bool:
    labels = hostname.strip(".").split(".")
    for index, label in enumerate(labels):
        if label in {
            "development",
            "internal",
            "intranet",
            "corp",
            "private",
            "localhost",
            "staging",
            "sandbox",
            "qa",
            "uat",
            "local",
        }:
            return True
        if "internal" in label:
            return True
        if label == "dev" and index < len(labels) - 1:
            return True
    return False
