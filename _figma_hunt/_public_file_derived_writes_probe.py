"""Authorization probes for derived write APIs on a public Make file."""

import io
import json
import sys
import urllib.error
import urllib.request


sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "https://www.figma.com"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
A_UID = "1666382703778278399"
B_UID = "1667396392129259941"
A_PUBLIC_MAKE = "5zb5YkoxMa09KpqOyuLcHD"
A_PRIVATE_FILE = "5Gs4PaTz11Hlk2sqVnidBG"
B_FILE = "xFETb3KJ8wh2U8wjD9jJeY"


def load_cookie(name):
    with io.open(name, encoding="utf-8") as handle:
        return handle.read().strip()


def call(method, path, body, file_key, uid=None, cookie=None):
    headers = {
        "User-Agent": UA,
        "Accept": "application/json",
        "Origin": BASE,
        "Referer": f"{BASE}/file/{file_key}",
        "Content-Type": "application/json",
        "X-Figma-User-ID": uid or "",
        "X-Figma-File-Key": file_key,
    }
    if cookie:
        headers["Cookie"] = cookie
    data = None if body is None else json.dumps(body).encode()
    request = urllib.request.Request(
        BASE + path,
        data=data,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, response.read().decode(errors="replace")
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode(errors="replace")


def summary(raw):
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return raw[:180]
    if not isinstance(value, dict):
        return f"json_type={type(value).__name__}"
    result = {"keys": sorted(value)}
    for key in ("status", "error", "message", "reason"):
        if key in value:
            result[key] = value[key]
    if isinstance(value.get("meta"), dict):
        result["meta_keys"] = sorted(value["meta"])
    return json.dumps(result, ensure_ascii=False)


cookie_a = load_cookie("ws_cookie_A_new.txt")
cookie_b = load_cookie("ws_cookie_B_new.txt")
actors = (
    ("A owner", A_UID, cookie_a),
    ("B viewer", B_UID, cookie_b),
    ("anonymous", None, None),
)

tests = (
    (
        "invalid cover URL",
        "POST",
        lambda key: f"/api/files/{key}/weave_cover_photo_from_url",
        {"url": "not-a-valid-url"},
    ),
    (
        "page thumbnail regeneration",
        "POST",
        lambda key: f"/api/files/{key}/page_thumbnails",
        {},
    ),
    (
        "reference ID",
        "POST",
        lambda key: f"/api/files/{key}/reference_id",
        {},
    ),
    (
        "video upload slot",
        "GET",
        lambda key: f"/api/files/{key}/videos/{'0' * 40}/upload",
        None,
    ),
    (
        "audio upload slot",
        "POST",
        lambda key: f"/api/files/{key}/audios/{'0' * 40}/upload",
        {},
    ),
)

for test_label, method, path_for, body in tests:
    print(f"\n== {test_label}: A public Make ==")
    for actor_label, uid, cookie in actors:
        code, raw = call(
            method,
            path_for(A_PUBLIC_MAKE),
            body,
            A_PUBLIC_MAKE,
            uid,
            cookie,
        )
        print(f"[{actor_label}] {code} {summary(raw)}")

print("\n== owner controls: invalid cover URL ==")
for label, key, uid, cookie in (
    ("A / A private", A_PRIVATE_FILE, A_UID, cookie_a),
    ("B / B private", B_FILE, B_UID, cookie_b),
    ("B / A private", A_PRIVATE_FILE, B_UID, cookie_b),
):
    code, raw = call(
        "POST",
        f"/api/files/{key}/weave_cover_photo_from_url",
        {"url": "not-a-valid-url"},
        key,
        uid,
        cookie,
    )
    print(f"[{label}] {code} {summary(raw)}")
