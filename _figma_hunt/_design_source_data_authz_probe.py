"""Probe Make design-source upload authorization without uploading content."""

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
FAKE_SHA1 = "0" * 40


def load_cookie(name):
    with io.open(name, encoding="utf-8") as handle:
        return handle.read().strip()


def call(method, path, file_key, uid=None, cookie=None, body=None):
    headers = {
        "User-Agent": UA,
        "Accept": "application/json",
        "Origin": BASE,
        "Referer": f"{BASE}/make/{file_key}",
        "X-Figma-User-ID": uid or "",
        "X-Figma-File-Key": file_key,
    }
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
    if cookie:
        headers["Cookie"] = cookie
    request = urllib.request.Request(BASE + path, headers=headers, data=data, method=method)
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
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
    result = {"keys": sorted(value), "status": value.get("status")}
    for key in ("error", "message", "reason"):
        if key in value:
            result[key] = value[key]
    meta = value.get("meta")
    if isinstance(meta, dict):
        result["meta_keys"] = sorted(meta)
        packages = meta.get("upload_packages")
        if isinstance(packages, dict):
            result["upload_package_count"] = len(packages)
            result["has_upload_url"] = any(
                isinstance(item, dict)
                and isinstance(item.get("package"), dict)
                and bool(item["package"].get("upload_url"))
                for item in packages.values()
            )
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
    print(f"\n== init uploads: {file_label} ==")
    for actor_label, uid, cookie in actors:
        code, raw = call(
            "POST",
            f"/api/design_source_data/{file_key}/init_uploads",
            file_key,
            uid,
            cookie,
            {"file_key": file_key, "content_sha1s": [FAKE_SHA1]},
        )
        print(f"[{actor_label}] {code} {summary(raw)}")

    print(f"== list fake blob: {file_label} ==")
    query = urllib.parse.urlencode(
        [("file_key", file_key), ("content_keys[]", "authz-probe-invalid")]
    )
    for actor_label, uid, cookie in actors:
        code, raw = call(
            "GET",
            f"/api/design_source_data/{file_key}/blobs?{query}",
            file_key,
            uid,
            cookie,
        )
        print(f"[{actor_label}] {code} {summary(raw)}")
