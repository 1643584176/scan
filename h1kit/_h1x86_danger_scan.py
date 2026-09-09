# -*- coding: utf-8 -*-
"""危险模式系统扫描:已有 16MB bundle(app+vendor+constants)(2026-09-09)"""
import os
import re

FILES = [
    r"D:\scan\h1kit\_h1x4_app.js",
    r"D:\scan\h1kit\_h1x4_vendor.js",
    r"D:\scan\h1kit\_h1x3_constants.js",
]

PATTERNS = {
    "innerHTML=": r"\.innerHTML\s*=",
    "outerHTML=": r"\.outerHTML\s*=",
    "insertAdjacentHTML": r"insertAdjacentHTML",
    "document.write": r"document\.write",
    "eval(": r"\beval\s*\(",
    "Function(": r"[^a-zA-Z]Function\s*\(",
    "postMessage": r"postMessage\s*\(",
    "localStorage": r"localStorage\s*\.\s*(get|set|remove)",
    "sessionStorage": r"sessionStorage\s*\.\s*(get|set|remove)",
    "atob-b64decode": r"atob\s*\(",
    "webpack_public_util": r"__webpack_require__",
    "sendBeacon": r"sendBeacon",
    "fetch_abs": r"fetch\s*\(\s*[\"']https?:",
    "XMLHttpRequest": r"new\s+XMLHttpRequest",
    "FormData": r"new\s+FormData",
    "credential": r"credentials\s*:",
    "withCredentials": r"withCredentials",
    "api_key/token_assign": r"(api[_-]?key|secret|token)\s*[:=]\s*[\"'][A-Za-z0-9_\-\.]{12,}[\"']",
    "sk_live/test": r"(sk|pk|rk)_(live|test)_[A-Za-z0-9]{16,}",
    "AKIA(aws)": r"AKIA[0-9A-Z]{16}",
    "ghp_github": r"gh[pousr]_[A-Za-z0-9]{20,}",
    "private_key_block": r"-----BEGIN (RSA |EC |)PRIVATE KEY-----",
    "TODO/FIXME": r"(TODO|FIXME|HACK|XXX)[:\s]",
    "console.log": r"console\.(log|debug|info)",
    "debugger": r"\bdebugger\b",
    "alert(": r"alert\s*\(",
    "open_redirect_sus": r"(location|href)\s*[=.]\s*.*(search|param|query|url)",
    "history.push": r"history\.(push|replace)State",
}

for fn in FILES:
    print(f"\n########## {os.path.basename(fn)}")
    with open(fn, "r", encoding="utf-8", errors="replace") as f:
        data = f.read()
    for label, pat in PATTERNS.items():
        hits = list(re.finditer(pat, data))
        if hits:
            print(f"\n-- {label}: {len(hits)}")
            for h in hits[:3]:
                ctx = data[max(0, h.start() - 100):h.start() + 150].replace("\n", " ")[:250]
                print(f"   > {ctx}")
