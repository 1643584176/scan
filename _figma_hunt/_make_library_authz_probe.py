"""Compare Make Library metadata and publication-status authorization."""

import io
import json
import sys
import urllib.error
import urllib.parse
import urllib.request


sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "https://www.figma.com"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
A_UID = "1666382703778278399"
B_UID = "1667396392129259941"
A_PUBLIC_MAKE = "5zb5YkoxMa09KpqOyuLcHD"
A_PRIVATE_FILE = "5Gs4PaTz11Hlk2sqVnidBG"


def load_cookie(name):
    with io.open(name, encoding="utf-8") as handle:
        return handle.read().strip()


def get(path, file_key, uid=None, cookie=None):
    headers = {
        "User-Agent": UA,
        "Accept": "application/json",
        "Referer": f"{BASE}/make/{file_key}",
        "X-Figma-User-ID": uid or "",
        "X-Figma-File-Key": file_key,
    }
    if cookie:
        headers["Cookie"] = cookie
    request = urllib.request.Request(BASE + path, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            return response.status, response.read().decode(errors="replace")
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode(errors="replace")


def parse(raw):
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def summary(raw):
    value = parse(raw)
    if not isinstance(value, dict):
        return raw[:180]
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
                result[f"{key}_ids"] = [
                    entry.get("id")
                    for entry in item
                    if isinstance(entry, dict) and entry.get("id")
                ][:10]
            elif isinstance(item, dict):
                result[f"{key}_count"] = len(item)
    return json.dumps(result, ensure_ascii=False)


cookie_a = load_cookie("ws_cookie_A_new.txt")
cookie_b = load_cookie("ws_cookie_B_new.txt")
actors = (
    ("A owner", A_UID, cookie_a),
    ("B viewer", B_UID, cookie_b),
    ("anonymous", None, None),
)

for file_label, file_key in (
    ("A public Make", A_PUBLIC_MAKE),
    ("A private file", A_PRIVATE_FILE),
):
    print(f"\n== libraries for {file_label} ==")
    owner_value = None
    query = urllib.parse.urlencode({"file_key": file_key})
    for actor_label, uid, cookie in actors:
        code, raw = get(f"/api/make/make_libraries?{query}", file_key, uid, cookie)
        print(f"[{actor_label}] {code} {summary(raw)}")
        if actor_label == "A owner" and code == 200:
            owner_value = parse(raw)

    meta = owner_value.get("meta", {}) if isinstance(owner_value, dict) else {}
    libraries = []
    for item in meta.values() if isinstance(meta, dict) else []:
        if isinstance(item, list):
            libraries.extend(entry for entry in item if isinstance(entry, dict))
    library_ids = [entry.get("id") for entry in libraries if entry.get("id")]
    for library_id in library_ids[:3]:
        print(f"\n== publication status {library_id} ==")
        status_query = urllib.parse.urlencode({"make_library_id": library_id})
        for actor_label, uid, cookie in actors:
            code, raw = get(
                f"/api/make/publish_make_library?{status_query}",
                file_key,
                uid,
                cookie,
            )
            print(f"[{actor_label}] {code} {summary(raw)}")
