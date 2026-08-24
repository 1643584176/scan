"""Check whether public-file derived resources survive link-access revocation."""

import io
import json
import sys
import urllib.error
import urllib.parse
import urllib.request


sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "https://www.figma.com"
FILE_KEY = "5zb5YkoxMa09KpqOyuLcHD"
THREAD_ID = "3564968b-35ee-451f-a087-4af2c00ef620"
A_UID = "1666382703778278399"
B_UID = "1667396392129259941"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"


def load_cookie(name):
    with io.open(name, encoding="utf-8") as handle:
        return handle.read().strip()


def request(method, path, uid=None, cookie=None, body=None):
    headers = {
        "Accept": "application/json",
        "Origin": BASE,
        "Referer": f"{BASE}/make/{FILE_KEY}",
        "User-Agent": UA,
        "X-Figma-File-Key": FILE_KEY,
        "X-Figma-User-ID": uid or "",
    }
    data = None
    if cookie:
        headers["Cookie"] = cookie
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
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
    meta = value.get("meta", value)
    result = {"top_keys": sorted(value)[:20]}
    if isinstance(meta, dict):
        for key in ("key", "name", "link_access", "can_edit", "can_view"):
            if key in meta:
                result[key] = meta[key]
        for key in ("threads", "make_versions"):
            if isinstance(meta.get(key), list):
                result[f"{key}_count"] = len(meta[key])
                result[f"{key}_ids"] = [
                    item.get("id") for item in meta[key][:5] if isinstance(item, dict)
                ]
    for key in ("error", "message", "status"):
        if key in value:
            result[key] = value[key]
    return json.dumps(result, ensure_ascii=False)


def set_link_access(cookie_a, value):
    status, raw = request(
        "PUT",
        f"/api/files/{FILE_KEY}",
        A_UID,
        cookie_a,
        {"key": FILE_KEY, "link_access": value},
    )
    print(f"[A set link_access={value}] {status} {summarize(raw)}")
    if status != 200:
        raise RuntimeError(f"link access update failed: {status}")


def probe_phase(label, cookie_a, cookie_b):
    query = urllib.parse.urlencode({"owner_id": FILE_KEY, "owner_type": "file"})
    paths = (
        ("file", f"/api/files/{FILE_KEY}"),
        ("metadata", f"/api/file_metadata/{FILE_KEY}"),
        ("threads", f"/api/ai_chat/threads?{query}"),
        (
            "versions",
            f"/api/ai_chat/{FILE_KEY}/make_versions/{THREAD_ID}?page_size=64",
        ),
    )
    for actor, uid, cookie in (
        ("A", A_UID, cookie_a),
        ("B", B_UID, cookie_b),
        ("anonymous", None, None),
    ):
        for resource, path in paths:
            status, raw = request("GET", path, uid, cookie)
            print(f"[{label} / {actor} / {resource}] {status} {summarize(raw)}")


def main():
    cookie_a = load_cookie("ws_cookie_A_new.txt")
    cookie_b = load_cookie("ws_cookie_B_new.txt")
    status, raw = request("GET", f"/api/files/{FILE_KEY}", A_UID, cookie_a)
    baseline = json.loads(raw).get("meta", {}) if status == 200 else {}
    original = baseline.get("link_access")
    print(f"[original] status={status} link_access={original!r}")
    if original != "view":
        raise RuntimeError("refusing to run: expected the owned test file to be public-view")

    probe_phase("public baseline", cookie_a, cookie_b)
    changed = False
    try:
        set_link_access(cookie_a, "inherit")
        changed = True
        probe_phase("after revocation", cookie_a, cookie_b)
    finally:
        if changed:
            set_link_access(cookie_a, original)
            status, raw = request("GET", f"/api/files/{FILE_KEY}", A_UID, cookie_a)
            restored = json.loads(raw).get("meta", {}).get("link_access")
            print(f"[restore verification] status={status} link_access={restored!r}")
            if status != 200 or restored != original:
                raise RuntimeError("owned test file was not restored")


if __name__ == "__main__":
    main()
