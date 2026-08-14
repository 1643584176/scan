"""foundry/weave 端点探测:B cookie,验证哪些端点不经过 AI 墙(只到参数校验层)
schema 来源:1037 chunk 模块 136858/24260(已确认导出映射)
"""
import io, json, urllib.request, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

CK = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
UID = "1667396392129259941"
PUB_KEY = "bv2nMIdFf4u3dESGail4sm"

def call(label, path, body=None, method="POST", file_key=PUB_KEY, uid=UID, extra=None):
    hdrs = {"User-Agent": UA, "Accept": "application/json",
            "Origin": "https://www.figma.com", "Referer": "https://www.figma.com/",
            "Content-Type": "application/json", "Cookie": CK,
            "X-Figma-Org-ID": "", "X-Figma-Team-ID": "",
            "X-Figma-Client-Lifecycle-ID": "probe",
            "Tsid": "probe", "X-Referer-Service": "web"}
    if uid: hdrs["X-Figma-User-ID"] = uid
    if file_key is not None: hdrs["X-Figma-File-Key"] = file_key
    if extra: hdrs.update(extra)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request("https://www.figma.com" + path, data=data, headers=hdrs, method=method)
    try:
        r = urllib.request.urlopen(req, timeout=12)
        resp = r.read().decode(errors='replace')
        print(f"[{label}] {r.status}  {len(resp)}B  {resp[:260]}")
    except urllib.error.HTTPError as e:
        resp = e.read().decode(errors='replace')
        print(f"[{label}] {e.code}  {resp[:260]}")
    except Exception as e:
        print(f"[{label}] !! {type(e).__name__} {str(e)[:80]}")

print("======== foundry/weave 端点探测(B cookie) ========")
# 1. weave/inspect = GET {id, version?} —— 昨天 POST 500,现在用 GET
call("weave/inspect GET", "/api/cortex/weave/inspect?id=test")
# 2. weave/inspect 无 id
call("weave/inspect 无id", "/api/cortex/weave/inspect")
# 3. debug-sandbox-status: {entityId?} 空 body
call("debug-sandbox-status 空", "/api/cortex/foundry/debug-sandbox-status", {})
# 4. keep-alive: 同 inspect schema {id}
call("keep-alive {id}", "/api/cortex/foundry/keep-alive", {"id": "test"})
# 5. reset: et={...d} 空
call("reset 空", "/api/cortex/foundry/reset", {})
# 6. clear-session: ed.H
call("clear-session 空", "/api/cortex/foundry/clear-session", {})
# 7. interrupt: ec.b
call("interrupt 空", "/api/cortex/foundry/interrupt", {})

print()
print("======== sessionId 行为测试(B cookie) ========")
import uuid
sid = str(uuid.uuid4())
print("random sessionId:", sid)
# clearSession: 完整必填字段 + 随机 sessionId
call("clearSession 随机sid", "/api/cortex/foundry/clear-session",
     {"sessionId": sid, "workloadName": "make", "entityId": "test"})
# interrupt: 完整必填字段 + 随机 sessionId
call("interrupt 随机sid", "/api/cortex/foundry/interrupt",
     {"sessionId": sid, "workloadName": "make", "revert": False})
# keep-alive 带 entityId
call("keep-alive entityId", "/api/cortex/foundry/keep-alive",
     {"entityId": "test", "workloadName": "make"})
# clearSession 空 sessionId
call("clearSession 空sid", "/api/cortex/foundry/clear-session",
     {"sessionId": "", "workloadName": "make"})

print()
print("======== sandbox 端点(B cookie) ========")
# sandbox: A schema, scopeType+scopeKey 成对
call("sandbox 空", "/api/cortex/foundry/sandbox", {})
call("sandbox scope", "/api/cortex/foundry/sandbox",
     {"scopeType": "global", "scopeKey": "test", "workloadConfig": {"workloadName": "make"}})
# install: j={autoUpdatePackages: bool, ...d}
call("install", "/api/cortex/foundry/install", {"autoUpdatePackages": True})
# get-updated-package-json: K
call("get-pkgjson", "/api/cortex/foundry/get-updated-package-json", {})
# sync: P
call("sync 空", "/api/cortex/foundry/sync", {})
# restart: B={fileKeyHash?...}
call("restart 空", "/api/cortex/foundry/restart", {})
# fs-read-file: ei={sboxdUrl, path, ...d}
call("fs-read-file 空", "/api/cortex/foundry/fs-read-file", {})
