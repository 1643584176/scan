# 实验J104: snapshot 详情完整字段 + 越权访问陌生 snapshotId + download 子端点枚举
import json, time, urllib.request, urllib.error, sys, base64
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

TOKEN = "vcp_REDACTED_PLACEHOLDER"
TEAM = "team_GIy1SZ444lspqeNbh4r8uAUg"
PROJ = "prj_iyw2xfjP3RKPT7n8b8c1tBIxxK5F"

def api(method, path, body=None, timeout=300):
    req = urllib.request.Request(f"https://api.vercel.com{path}", method=method)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Content-Type", "application/json")
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=timeout) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:800]
    except Exception as e:
        return -1, f"EXC {type(e).__name__}: {e}"

# 拿自己的一个 snapshotId
c, r = api("GET", f"/v2/sandboxes?teamId={TEAM}&project={PROJ}")
sbx = json.loads(r)["sandboxes"]
own_snap = next((s["currentSnapshotId"] for s in sbx if s.get("currentSnapshotId")), None)
own_sbx = next((s["currentSessionId"] for s in sbx if s.get("currentSessionId")), None)
print("own snapshot:", own_snap, flush=True)
print("own session:", own_sbx, flush=True)

# --- [A] 完整 snapshot 详情 ---
print("\n== [A] GET /v2/sandboxes/snapshots/{own} 完整 ==", flush=True)
c, r = api("GET", f"/v2/sandboxes/snapshots/{own_snap}?teamId={TEAM}&project={PROJ}")
print(f"  {c}: {r}", flush=True)

# --- [B] 越权: 陌生 snapshotId (格式正确) ---
print("\n== [B] 陌生 snapshotId 越权 ==", flush=True)
fakes = ["snap_zzzzzzzzzzzzzzzzzzzzzzzzzz",
         "snap_AAAAAAAAAAAAAAAAAAAAAAAAAA",
         "snap_9DuDa2AVJPoUO4jSAMRjKJMgvBxR",  # 改尾字符
         "snap_00000000000000000000000000"]
for fake in fakes:
    c, r = api("GET", f"/v2/sandboxes/snapshots/{fake}?teamId={TEAM}&project={PROJ}")
    print(f"  [{fake[:14]}...] {c}: {r[:250]}", flush=True)
    time.sleep(0.3)

# --- [C] 子端点枚举 (download/content/archive...) ---
print("\n== [C] snapshot 子端点 ==", flush=True)
if own_snap:
    for sub in ["download", "content", "archive", "url", "export", "files", "tar", "attachments"]:
        c, r = api("GET", f"/v2/sandboxes/snapshots/{own_snap}/{sub}?teamId={TEAM}&project={PROJ}")
        print(f"  /{sub} -> {c}: {r[:200]}", flush=True)
        time.sleep(0.3)
    # POST 变体
    for sub in ["download", "export", "restore"]:
        c, r = api("POST", f"/v2/sandboxes/snapshots/{own_snap}/{sub}?teamId={TEAM}&project={PROJ}", {})
        print(f"  POST /{sub} -> {c}: {r[:200]}", flush=True)
        time.sleep(0.3)

# --- [D] 列表快照端点 ---
print("\n== [D] snapshot 列表 ==", flush=True)
for path in [f"/v2/sandboxes/snapshots?teamId={TEAM}&project={PROJ}",
             f"/v2/sandboxes/{own_sbx}/snapshots?teamId={TEAM}&project={PROJ}",
             f"/v2/sandboxes/sessions/{own_sbx}/snapshots?teamId={TEAM}&project={PROJ}"]:
    c, r = api("GET", path)
    print(f"  GET {path.split('?')[0][:60]} -> {c}: {r[:300]}", flush=True)
    time.sleep(0.3)

# --- [E] session 相关: 陌生 sessionId 调 cmd? ---
print("\n== [E] 用其他沙箱的 sessionId 调 cmd (越权) ==", flush=True)
other_sid = None
for s in sbx:
    if s["currentSessionId"] != own_sbx:
        other_sid = s["currentSessionId"]
        break
print("  other session:", other_sid, flush=True)
if other_sid:
    body = {"command": "echo", "args": ["pwn"], "wait": True, "logs": True, "timeout": 60}
    c, r = api("POST", f"/v2/sandboxes/sessions/{other_sid}/cmd?teamId={TEAM}", body)
    print(f"  cmd on other sandbox -> {c}: {r[:250]}", flush=True)
    # 陌生 sessionId
    c, r = api("POST", f"/v2/sandboxes/sessions/sbx_zzzzzzzzzzzzzzzzzzzzzzzzzz/cmd?teamId={TEAM}", body)
    print(f"  cmd on fake session -> {c}: {r[:250]}", flush=True)

print("\ndone", flush=True)
