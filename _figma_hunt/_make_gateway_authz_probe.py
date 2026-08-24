"""Compare Make AI gateway token authorization without printing credentials."""

import hashlib
import io
import json
import sys
import urllib.error
import urllib.request


sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "https://www.figma.com"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
)
A_UID = "1666382703778278399"
B_UID = "1667396392129259941"
A_PUBLIC_MAKE = "5zb5YkoxMa09KpqOyuLcHD"
A_PRIVATE_FILE = "5Gs4PaTz11Hlk2sqVnidBG"


def load_cookie(name):
    with io.open(name, encoding="utf-8") as handle:
        return handle.read().strip()


def summarize(raw):
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return raw[:180]
    if not isinstance(value, dict):
        return f"json_type={type(value).__name__}"
    summary = {"keys": sorted(value)}
    token = value.get("token")
    if isinstance(token, str):
        summary["token_len"] = len(token)
        summary["token_sha256_prefix"] = hashlib.sha256(token.encode()).hexdigest()[:12]
    if "expiresAt" in value:
        summary["has_expiry"] = value["expiresAt"] is not None
    for key in ("error", "message", "status", "cortex_error"):
        if key in value:
            summary[key] = value[key]
    return json.dumps(summary, ensure_ascii=False)


def call(label, endpoint, file_key, uid=None, cookie=None, owner_context=False):
    headers = {
        "User-Agent": UA,
        "Accept": "application/json",
        "Origin": BASE,
        "Referer": f"{BASE}/make/{file_key}",
        "Content-Type": "application/json",
        "X-Figma-File-Key": file_key,
        "X-Figma-User-ID": uid or "",
        "X-Figma-Org-ID": "",
        "X-Figma-Team-ID": "",
        "X-Figma-Client-Lifecycle-ID": "authz-probe",
        "X-Figma-Persistent-Entity-ID": "",
        "X-Figma-Cortex-Client-Generated-Request-UUID": "authz-probe",
        "Tsid": "authz-probe",
        "X-Referer-Service": "web",
    }
    if owner_context:
        headers["X-Figma-Owner-ID"] = file_key
        headers["X-Figma-Owner-Type"] = "file"
    if cookie:
        headers["Cookie"] = cookie
    request = urllib.request.Request(
        BASE + endpoint,
        data=b"{}",
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            raw = response.read().decode(errors="replace")
            print(f"[{label}] {response.status} {summarize(raw)}")
    except urllib.error.HTTPError as error:
        raw = error.read().decode(errors="replace")
        print(f"[{label}] {error.code} {summarize(raw)}")
    except Exception as error:
        print(f"[{label}] ERROR {type(error).__name__}: {str(error)[:160]}")


cookie_a = load_cookie("ws_cookie_A_new.txt")
cookie_b = load_cookie("ws_cookie_B_new.txt")

for path in (
    "/api/cortex/make/ai_gateway_token",
    "/api/cortex/make/ai_gateway_token_file",
):
    print(f"\n== {path} ==")
    call("A owner / public Make", path, A_PUBLIC_MAKE, A_UID, cookie_a, True)
    call("B viewer / A public Make", path, A_PUBLIC_MAKE, B_UID, cookie_b, True)
    call("anonymous / A public Make", path, A_PUBLIC_MAKE, owner_context=True)
    call("A owner / private file", path, A_PRIVATE_FILE, A_UID, cookie_a, True)
    call("B / A private file", path, A_PRIVATE_FILE, B_UID, cookie_b, True)
