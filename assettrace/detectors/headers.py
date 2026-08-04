from __future__ import annotations

import re

from assettrace.models import AssetSnapshot, DetectorResult, FindingDraft


class SecurityHeadersDetector:
    key = "security-headers"
    version = "1.1.0"
    supported_kinds = frozenset({"page"})

    def analyze(self, snapshot: AssetSnapshot) -> DetectorResult:
        headers = {key.lower(): value for key, value in snapshot.headers.items()}
        findings: list[FindingDraft] = []
        csp = headers.get("content-security-policy", "")
        hsts = headers.get("strict-transport-security", "")
        acao = headers.get("access-control-allow-origin", "").strip()
        acac = headers.get("access-control-allow-credentials", "").lower()
        acam = headers.get("access-control-allow-methods", "").upper()
        acah = headers.get("access-control-allow-headers", "").lower()
        cache_control = headers.get("cache-control", "").lower()
        set_cookie = headers.get("set-cookie", "")

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

        has_frame_ancestors = "frame-ancestors" in csp.lower()
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
        elif snapshot.url.startswith("https://"):
            max_age = _parse_hsts_max_age(hsts)
            if max_age is not None and max_age < 31536000:
                findings.append(
                    FindingDraft(
                        dedupe_key="hsts-max-age-too-short",
                        title="HTTP Strict Transport Security max-age is shorter than one year",
                        category="transport-security",
                        severity="low",
                        confidence="high",
                        evidence=(
                            "Strict-Transport-Security is present but its "
                            f"max-age is only {max_age} seconds."
                        ),
                        remediation=(
                            "Raise HSTS max-age to at least 31536000 after "
                            "confirming the application and its subdomains are HTTPS-ready."
                        ),
                    )
                )

        lowered_csp = csp.lower()
        if csp:
            if "'unsafe-inline'" in lowered_csp or "'unsafe-eval'" in lowered_csp:
                unsafe_tokens = _join_present(
                    lowered_csp, ("'unsafe-inline'", "'unsafe-eval'")
                )
                findings.append(
                    FindingDraft(
                        dedupe_key="csp-unsafe-directives",
                        title="Content Security Policy allows unsafe script execution",
                        category="security-misconfiguration",
                        severity="medium",
                        confidence="high",
                        evidence=(
                            "Content-Security-Policy contains "
                            f"{unsafe_tokens}."
                        ),
                        remediation=(
                            "Remove unsafe CSP script allowances and replace "
                            "them with nonces, hashes, or stricter script loading."
                        ),
                    )
                )
            if "default-src" not in lowered_csp:
                findings.append(
                    FindingDraft(
                        dedupe_key="csp-default-src-missing",
                        title="Content Security Policy does not define default-src",
                        category="security-misconfiguration",
                        severity="low",
                        confidence="high",
                        evidence="Content-Security-Policy is present without a default-src fallback.",
                        remediation="Define default-src to ensure new resource types inherit a restrictive baseline.",
                    )
                )
            if "object-src" not in lowered_csp:
                findings.append(
                    FindingDraft(
                        dedupe_key="csp-object-src-missing",
                        title="Content Security Policy does not restrict plugin content",
                        category="security-misconfiguration",
                        severity="low",
                        confidence="high",
                        evidence="Content-Security-Policy does not define object-src.",
                        remediation="Set object-src 'none' unless legacy plugin content is explicitly required.",
                    )
                )
            if "base-uri" not in lowered_csp:
                findings.append(
                    FindingDraft(
                        dedupe_key="csp-base-uri-missing",
                        title="Content Security Policy does not restrict base-uri",
                        category="security-misconfiguration",
                        severity="low",
                        confidence="high",
                        evidence="Content-Security-Policy does not define base-uri.",
                        remediation="Set base-uri 'self' or a narrower allow-list.",
                    )
                )

        referrer_policy = headers.get("referrer-policy", "").lower()
        if referrer_policy in {"unsafe-url", "no-referrer-when-downgrade"}:
            findings.append(
                FindingDraft(
                    dedupe_key="referrer-policy-weak",
                    title="Referrer policy is overly permissive",
                    category="security-misconfiguration",
                    severity="low",
                    confidence="high",
                    evidence=f"Referrer-Policy is set to {referrer_policy}.",
                    remediation="Prefer strict-origin-when-cross-origin or a stricter policy for sensitive applications.",
                )
            )

        if acao == "*" and acac == "true":
            findings.append(
                FindingDraft(
                    dedupe_key="cors-wildcard-with-credentials",
                    title="CORS allows any origin while credentials are enabled",
                    category="cors-misconfiguration",
                    severity="high",
                    confidence="high",
                    evidence=(
                        "Access-Control-Allow-Origin is '*' and "
                        "Access-Control-Allow-Credentials is true."
                    ),
                    remediation="Disable credentialed CORS for wildcard origins and allow only explicit trusted origins.",
                )
            )
        elif acao == "*":
            findings.append(
                FindingDraft(
                    dedupe_key="cors-wildcard-origin",
                    title="CORS allows any origin",
                    category="cors-misconfiguration",
                    severity="medium",
                    confidence="high",
                    evidence="Access-Control-Allow-Origin is '*'.",
                    remediation="Limit cross-origin access to the minimum explicit origin allow-list.",
                )
            )
        elif acao == "null":
            findings.append(
                FindingDraft(
                    dedupe_key="cors-null-origin",
                    title="CORS allows the null origin",
                    category="cors-misconfiguration",
                    severity="medium",
                    confidence="high",
                    evidence="Access-Control-Allow-Origin is 'null'.",
                    remediation="Do not allow null origins unless a documented sandboxed flow requires it.",
                )
            )

        if acao in {"*", "null"} and any(
            method in acam for method in ("PUT", "PATCH", "DELETE")
        ):
            findings.append(
                FindingDraft(
                    dedupe_key="cors-broad-methods",
                    title="CORS preflight allows broad state-changing methods",
                    category="cors-misconfiguration",
                    severity="medium",
                    confidence="high",
                    evidence=(
                        "Cross-origin access is broadly allowed and "
                        f"Access-Control-Allow-Methods includes {acam or 'multiple methods'}."
                    ),
                    remediation="Restrict CORS methods to the minimum read-only set required by the application.",
                )
            )
        if acao in {"*", "null"} and any(
            token in acah for token in ("authorization", "x-api-key")
        ):
            findings.append(
                FindingDraft(
                    dedupe_key="cors-sensitive-headers",
                    title="CORS allows sensitive request headers from broad origins",
                    category="cors-misconfiguration",
                    severity="medium",
                    confidence="high",
                    evidence=(
                        "Access-Control-Allow-Headers permits "
                        f"{_join_present(acah, ('authorization', 'x-api-key'))} from a broad origin policy."
                    ),
                    remediation="Allow sensitive headers only for a tight origin allow-list.",
                )
            )

        if "x-powered-by" in headers:
            findings.append(
                FindingDraft(
                    dedupe_key="x-powered-by-exposed",
                    title="Response exposes X-Powered-By",
                    category="security-misconfiguration",
                    severity="info",
                    confidence="high",
                    evidence=f"X-Powered-By is set to {headers['x-powered-by']}.",
                    remediation="Remove framework-identifying response headers unless they are intentionally required.",
                )
            )

        cookie_findings = _cookie_findings(set_cookie, snapshot.url.startswith("https://"))
        findings.extend(cookie_findings)

        if set_cookie and _cache_policy_looks_risky(cache_control):
            findings.append(
                FindingDraft(
                    dedupe_key="session-response-cacheable",
                    title="Response sets cookies without a protective cache policy",
                    category="cache-policy",
                    severity="medium",
                    confidence="medium",
                    evidence=(
                        "The response sets cookies while Cache-Control is "
                        f"{cache_control or 'absent'}."
                    ),
                    remediation="Use Cache-Control: no-store for authenticated or session-establishing responses.",
                )
            )

        return DetectorResult(
            findings=findings,
            facts={
                "access_control_allow_origin": acao,
                "cache_control": cache_control,
                "present_security_headers": sorted(
                    key
                    for key in headers
                    if key
                    in {
                        "access-control-allow-credentials",
                        "access-control-allow-headers",
                        "access-control-allow-methods",
                        "access-control-allow-origin",
                        "content-security-policy",
                        "permissions-policy",
                        "referrer-policy",
                        "set-cookie",
                        "strict-transport-security",
                        "x-content-type-options",
                        "x-frame-options",
                    }
                )
            },
        )


def _parse_hsts_max_age(value: str) -> int | None:
    match = re.search(r"max-age\s*=\s*(\d+)", value, re.IGNORECASE)
    if not match:
        return None
    return int(match.group(1))


def _join_present(text: str, markers: tuple[str, ...]) -> str:
    return ", ".join(marker for marker in markers if marker in text)


def _cookie_findings(raw_header: str, is_https: bool) -> list[FindingDraft]:
    findings: list[FindingDraft] = []
    if not raw_header:
        return findings
    for index, cookie in enumerate(_split_cookies(raw_header), start=1):
        lowered = cookie.lower()
        name = cookie.split("=", 1)[0].strip() or f"cookie-{index}"
        if is_https and "secure" not in lowered:
            findings.append(
                FindingDraft(
                    dedupe_key=f"cookie-secure-missing:{name}",
                    title="Cookie is missing the Secure attribute",
                    category="cookie-security",
                    severity="medium",
                    confidence="high",
                    evidence=f"Set-Cookie for {name} does not include Secure.",
                    remediation="Mark cookies Secure so they are not sent over plaintext HTTP.",
                )
            )
        if "httponly" not in lowered:
            findings.append(
                FindingDraft(
                    dedupe_key=f"cookie-httponly-missing:{name}",
                    title="Cookie is missing the HttpOnly attribute",
                    category="cookie-security",
                    severity="low",
                    confidence="high",
                    evidence=f"Set-Cookie for {name} does not include HttpOnly.",
                    remediation="Mark cookies HttpOnly unless client-side JavaScript access is intentionally required.",
                )
            )
        same_site = _extract_samesite(lowered)
        if same_site is None:
            findings.append(
                FindingDraft(
                    dedupe_key=f"cookie-samesite-missing:{name}",
                    title="Cookie is missing the SameSite attribute",
                    category="cookie-security",
                    severity="low",
                    confidence="high",
                    evidence=f"Set-Cookie for {name} does not include SameSite.",
                    remediation="Set SameSite=Lax or SameSite=Strict unless cross-site use is explicitly required.",
                )
            )
        elif same_site == "none" and "secure" not in lowered:
            findings.append(
                FindingDraft(
                    dedupe_key=f"cookie-samesite-none-insecure:{name}",
                    title="Cookie uses SameSite=None without Secure",
                    category="cookie-security",
                    severity="medium",
                    confidence="high",
                    evidence=f"Set-Cookie for {name} uses SameSite=None without Secure.",
                    remediation="Pair SameSite=None only with Secure cookies.",
                )
            )
    return findings


def _split_cookies(raw_header: str) -> list[str]:
    return [
        item.strip()
        for item in re.split(r",\s*(?=[^;,\s]+=)", raw_header)
        if item.strip()
    ]


def _extract_samesite(lowered_cookie: str) -> str | None:
    match = re.search(r"samesite\s*=\s*(strict|lax|none)", lowered_cookie)
    if not match:
        return None
    return match.group(1)


def _cache_policy_looks_risky(cache_control: str) -> bool:
    if not cache_control:
        return True
    if "no-store" in cache_control or "private" in cache_control:
        return False
    return "public" in cache_control or "max-age" in cache_control or "s-maxage" in cache_control
