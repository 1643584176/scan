from __future__ import annotations

import json

from assettrace.detectors.javascript import SECRET_PATTERNS
from assettrace.models import AssetSnapshot, DetectorResult, FindingDraft


class SourceMapDetector:
    key = "source-map-static"
    version = "1.0.0"
    supported_kinds = frozenset({"source-map"})

    def analyze(self, snapshot: AssetSnapshot) -> DetectorResult:
        try:
            data = json.loads(snapshot.text)
        except json.JSONDecodeError:
            return DetectorResult(facts={"valid_source_map": False})

        sources = data.get("sources")
        sources_content = data.get("sourcesContent")
        if not isinstance(sources, list):
            sources = []
        if not isinstance(sources_content, list):
            sources_content = []

        embedded_sources = [
            content for content in sources_content if isinstance(content, str)
        ]
        findings: list[FindingDraft] = []
        if embedded_sources:
            findings.append(
                FindingDraft(
                    dedupe_key="embedded-source-code",
                    title="Source map exposes embedded source code",
                    category="source-map-exposure",
                    severity="info",
                    confidence="high",
                    evidence=(
                        f"Source map contains {len(embedded_sources)} embedded "
                        "source files. No sensitive content has been assumed."
                    ),
                    remediation=(
                        "Remove production source maps or omit sourcesContent "
                        "when the source is not intended to be public."
                    ),
                    location=snapshot.url,
                )
            )

        combined_source = "\n".join(embedded_sources)
        for secret_type, pattern, title in SECRET_PATTERNS:
            for match_index, match in enumerate(
                pattern.finditer(combined_source), start=1
            ):
                findings.append(
                    FindingDraft(
                        dedupe_key=f"{secret_type}:{match_index}",
                        title=f"{title} source map",
                        category="secret-exposure",
                        severity="critical",
                        confidence="high",
                        evidence=(
                            f"Matched {secret_type} in embedded source: "
                            f"{_redact(match.group(0))}"
                        ),
                        remediation=(
                            "Revoke and rotate the credential, then remove it "
                            "from both source files and production artifacts."
                        ),
                        location=snapshot.url,
                    )
                )

        return DetectorResult(
            findings=findings,
            facts={
                "valid_source_map": True,
                "source_count": len(sources),
                "embedded_source_count": len(embedded_sources),
            },
        )


def _redact(value: str) -> str:
    if len(value) <= 8:
        return "[redacted]"
    return f"{value[:4]}...{value[-4:]}"
