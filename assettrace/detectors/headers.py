from __future__ import annotations

from assettrace.models import AssetSnapshot, DetectorResult, FindingDraft


class SecurityHeadersDetector:
    key = "security-headers"
    version = "1.0.0"
    supported_kinds = frozenset({"page"})

    def analyze(self, snapshot: AssetSnapshot) -> DetectorResult:
        headers = {key.lower(): value for key, value in snapshot.headers.items()}
        findings: list[FindingDraft] = []

        checks = (
            (
                "content-security-policy",
                "Content Security Policy is missing",
                "csp-missing",
                "medium",
                "Define a restrictive Content-Security-Policy and avoid unsafe fallbacks.",
            ),
            (
                "x-content-type-options",
                "MIME sniffing protection is missing",
                "nosniff-missing",
                "low",
                "Return X-Content-Type-Options: nosniff.",
            ),
            (
                "referrer-policy",
                "Referrer policy is missing",
                "referrer-policy-missing",
                "low",
                "Set an explicit Referrer-Policy appropriate for the application.",
            ),
        )
        for header, title, dedupe_key, severity, remediation in checks:
            if header not in headers:
                findings.append(
                    FindingDraft(
                        dedupe_key=dedupe_key,
                        title=title,
                        category="security-misconfiguration",
                        severity=severity,
                        confidence="high",
                        evidence=f"Response does not contain {header}.",
                        remediation=remediation,
                    )
                )

        has_frame_ancestors = "frame-ancestors" in headers.get(
            "content-security-policy", ""
        ).lower()
        if "x-frame-options" not in headers and not has_frame_ancestors:
            findings.append(
                FindingDraft(
                    dedupe_key="framing-control-missing",
                    title="Framing protection is missing",
                    category="clickjacking",
                    severity="medium",
                    confidence="high",
                    evidence="Neither X-Frame-Options nor CSP frame-ancestors is present.",
                    remediation="Set CSP frame-ancestors; keep X-Frame-Options for legacy clients.",
                )
            )

        if snapshot.url.startswith("https://") and "strict-transport-security" not in headers:
            findings.append(
                FindingDraft(
                    dedupe_key="hsts-missing",
                    title="HTTP Strict Transport Security is missing",
                    category="transport-security",
                    severity="low",
                    confidence="high",
                    evidence="HTTPS response does not contain Strict-Transport-Security.",
                    remediation="Enable HSTS after confirming all application traffic supports HTTPS.",
                )
            )

        return DetectorResult(
            findings=findings,
            facts={
                "present_security_headers": sorted(
                    key
                    for key in headers
                    if key
                    in {
                        "content-security-policy",
                        "permissions-policy",
                        "referrer-policy",
                        "strict-transport-security",
                        "x-content-type-options",
                        "x-frame-options",
                    }
                )
            },
        )
