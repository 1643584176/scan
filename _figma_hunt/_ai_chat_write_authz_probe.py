"""Probe whether a view-only user can mutate a public Make chat thread."""

import io
import json
import sys
import urllib.error
import urllib.parse
import urllib.request


sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "https://www.figma.com"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
)
A_UID = "1666382703778278399"
B_UID = "1667396392129259941"
FILE_KEY = "5zb5YkoxMa09KpqOyuLcHD"
THREAD_ID = "3564968b-35ee-451f-a087-4af2c00ef620"


def load_cookie(name):
    with io.open(name, encoding="utf-8") as handle:
        return handle.read().strip()


def request(method, path, uid=None, cookie=None, body=None):
    headers = {
        "User-Agent": UA,
        "Accept": "application/json",
        "Origin": BASE,
        "Referer": f"{BASE}/make/{FILE_KEY}",
        "X-Figma-User-ID": uid or "",
        "X-Figma-File-Key": FILE_KEY,
    }
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
    if cookie:
        headers["Cookie"] = cookie
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            return response.status, response.read().decode(errors="replace")
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode(errors="replace")


def safe_summary(raw):
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return raw[:200]
    if not isinstance(value, dict):
        return f"json_type={type(value).__name__}"
    result = {"keys": sorted(value)}
    meta = value.get("meta")
    if isinstance(meta, dict):
        result["meta_keys"] = sorted(meta)
        threads = meta.get("threads")
        if isinstance(threads, list):
            result["threads"] = [
                {
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "privacy_mode": item.get("privacy_mode"),
                    "thread_type": item.get("thread_type"),
                }
                for item in threads
                if isinstance(item, dict)
            ]
        versions = meta.get("make_versions")
        if isinstance(versions, list):
            result["make_versions"] = [
                {
                    "id": item.get("id"),
                    "version_number": item.get("version_number"),
                    "title": item.get("title"),
                    "favorited": item.get("favorited"),
                    "has_snapshot": bool(
                        item.get("code_snapshot_key") or item.get("git_sha")
                    ),
                }
                for item in versions
                if isinstance(item, dict)
            ]
    for key in ("error", "message", "status"):
        if key in value:
            result[key] = value[key]
    return json.dumps(result, ensure_ascii=False)


cookie_a = load_cookie("ws_cookie_A_new.txt")
cookie_b = load_cookie("ws_cookie_B_new.txt")
query = urllib.parse.urlencode({"owner_id": FILE_KEY, "owner_type": "file"})

owner_title = None
baseline_version = None
for label, uid, cookie in (
    ("A owner", A_UID, cookie_a),
    ("B viewer", B_UID, cookie_b),
    ("anonymous", None, None),
):
    status, raw = request("GET", f"/api/ai_chat/threads?{query}", uid, cookie)
    print(f"[GET threads / {label}] {status} {safe_summary(raw)}")
    if label == "A owner" and status == 200:
        try:
            threads = json.loads(raw).get("meta", {}).get("threads", [])
            thread = next(item for item in threads if item.get("id") == THREAD_ID)
            if isinstance(thread.get("title"), str):
                owner_title = thread["title"]
        except (AttributeError, StopIteration, TypeError, ValueError):
            pass

if owner_title is None:
    print("[PUT title] skipped: owner baseline did not expose a string title")
else:
    same_title_body = {
        "owner_id": FILE_KEY,
        "owner_type": "file",
        "title": owner_title,
    }
    for label, uid, cookie in (
        ("A owner same-title baseline", A_UID, cookie_a),
        ("B viewer same-title probe", B_UID, cookie_b),
        ("anonymous same-title probe", None, None),
    ):
        status, raw = request(
            "PUT",
            f"/api/ai_chat/threads/{THREAD_ID}/title",
            uid,
            cookie,
            same_title_body,
        )
        print(f"[PUT title / {label}] {status} {safe_summary(raw)}")

for label, uid, cookie in (
    ("A owner same-privacy baseline", A_UID, cookie_a),
    ("B viewer same-privacy probe", B_UID, cookie_b),
    ("anonymous same-privacy probe", None, None),
):
    status, raw = request(
        "POST",
        f"/api/ai_chat/{FILE_KEY}/threads/{THREAD_ID}/privacy_mode",
        uid,
        cookie,
        {"privacy_mode": "file"},
    )
    print(f"[POST privacy / {label}] {status} {safe_summary(raw)}")

for label, uid, cookie in (
    ("A owner versions", A_UID, cookie_a),
    ("B viewer versions", B_UID, cookie_b),
    ("anonymous versions", None, None),
):
    status, raw = request(
        "GET",
        f"/api/ai_chat/{FILE_KEY}/make_versions/{THREAD_ID}?page_size=64",
        uid,
        cookie,
    )
    print(f"[GET versions / {label}] {status} {safe_summary(raw)}")
    if label == "A owner versions" and status == 200:
        try:
            versions = json.loads(raw).get("meta", {}).get("make_versions", [])
            if versions:
                baseline_version = versions[0]
        except (AttributeError, TypeError, ValueError):
            pass

if not isinstance(baseline_version, dict) or not baseline_version.get("id"):
    print("[PUT version] skipped: no baseline version")
else:
    update_body = {
        "file_key": FILE_KEY,
        "make_version_id": baseline_version["id"],
    }
    if isinstance(baseline_version.get("title"), str):
        update_body["title"] = baseline_version["title"]
    else:
        update_body["favorited"] = bool(baseline_version.get("favorited"))
    for label, uid, cookie in (
        ("A owner same-value baseline", A_UID, cookie_a),
        ("B viewer same-value probe", B_UID, cookie_b),
        ("anonymous same-value probe", None, None),
    ):
        status, raw = request(
            "PUT",
            f"/api/ai_chat/{FILE_KEY}/make_versions/{baseline_version['id']}/update",
            uid,
            cookie,
            update_body,
        )
        print(f"[PUT version / {label}] {status} {safe_summary(raw)}")
