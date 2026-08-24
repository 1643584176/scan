# -*- coding: utf-8 -*-
"""公开 Weave 文件: 匿名 vs B 的 AI 端点权限差异
验证:
 1. 匿名 make_versions (A的公开Weave) —— 文件公开时版本是否公开
 2. 匿名 threads 列表 —— 对照 B 的 403(AI权限)
 3. 匿名 file_metadata 类接口
 4. B 打开文件时 git 请求的真实认证头(从 playwright 抓)
"""
import io, json, sys, urllib.error, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://www.figma.com"
A_MAKE = "5zb5YkoxMa09KpqOyuLcHD"
A_THREAD = "28e728c0-dd4d-46e4-9b34-26cfb69e0aed"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151.0.0.0 Safari/537.36"


def load(path):
    return io.open(path, encoding='utf-8').read().strip().replace('\n', '; ')


BC = load('ws_cookie_B_new.txt')


def call(label, method, path, cookie=None, query=None):
    headers = {"User-Agent": UA, "Accept": "application/json", "Origin": BASE,
               "Referer": BASE + "/make/" + A_MAKE}
    if cookie:
        headers["Cookie"] = cookie
    url = BASE + path
    if query:
        url += "?" + urllib.parse.urlencode(query)
    req = urllib.request.Request(url, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            raw = r.read().decode(errors='replace')
            print(f"[{label}] HTTP {r.status} {raw[:500]}")
            return r.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors='replace')
        print(f"[{label}] HTTP {e.code} {raw[:400]}")
        return e.code, raw
    except Exception as e:
        print(f"[{label}] ❌ {type(e).__name__}: {str(e)[:120]}")
        return None, str(e)


print("======== 1. make_versions 匿名 vs B ========")
call("匿名 make_versions", "GET", f"/api/ai_chat/{A_MAKE}/make_versions/{A_THREAD}")
call("B make_versions", "GET", f"/api/ai_chat/{A_MAKE}/make_versions/{A_THREAD}", cookie=BC)

print("\n======== 2. threads 列表 匿名 vs B ========")
call("匿名 threads", "GET", "/api/ai_chat/threads", query={"owner_id": A_MAKE, "owner_type": "file"})
call("B threads", "GET", "/api/ai_chat/threads", cookie=BC,
     query={"owner_id": A_MAKE, "owner_type": "file"})

print("\n======== 3. threads attachments 匿名 ========")
call("匿名 attachments", "GET", f"/api/ai_chat/threads/{A_THREAD}/attachments")

print("\n======== 4. messages 匿名 ========")
call("匿名 messages", "GET", f"/api/ai_chat/messages/{A_THREAD}",
     query={"owner_id": A_MAKE, "owner_type": "file"})
