# 实验J103: snapshot 恢复/引用面 + cmd 接口参数面 (environment/workingDirectory)
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
        return e.code, e.read().decode()[:600]
    except Exception as e:
        return -1, f"EXC {type(e).__name__}: {e}"

# --- [A] 完整沙箱列表响应,提取所有字段 ---
print("== [A] GET /v2/sandboxes 完整响应 ==", flush=True)
c, r = api("GET", f"/v2/sandboxes?teamId={TEAM}&project={PROJ}")
print(f"  {c}", flush=True)
try:
    sbx = json.loads(r)
    for s in sbx.get("sandboxes", [])[:3]:
        print(f"  keys: {sorted(s.keys())}", flush=True)
        print(f"  {json.dumps(s)[:400]}", flush=True)
except Exception as e:
    print(f"  parse fail: {r[:300]}", flush=True)

snap = None
try:
    sbx = json.loads(r)
    for s in sbx.get("sandboxes", []):
        if s.get("currentSnapshotId"):
            snap = s["currentSnapshotId"]
            break
except Exception:
    pass
print("  first snapshot:", snap, flush=True)

# --- [B] snapshot 端点枚举 ---
print("\n== [B] snapshot 端点 ==", flush=True)
if snap:
    for path in [f"/v2/snapshots/{snap}?teamId={TEAM}&project={PROJ}",
                 f"/v2/sandboxes/snapshots/{snap}?teamId={TEAM}&project={PROJ}",
                 f"/v2/sandboxes/snapshot/{snap}?teamId={TEAM}&project={PROJ}"]:
        c, r = api("GET", path)
        print(f"  GET {path.split('?')[0]} -> {c}: {r[:250]}", flush=True)
        time.sleep(0.3)
    # 陌生 snapshot 越权
    for fake in ["snap_00000000000000000000000000", "snap_test", "snap_AAAAAAAAAAAAAAAAAAAAAAAAAAAA"]:
        c, r = api("GET", f"/v2/snapshots/{fake}?teamId={TEAM}&project={PROJ}")
        print(f"  GET /v2/snapshots/{fake[:12]}... -> {c}: {r[:200]}", flush=True)
        time.sleep(0.3)

# --- [C] 创建沙箱带 snapshotId / 恢复端点 ---
print("\n== [C] snapshot 恢复端点 ==", flush=True)
NAME = "expj103"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
if snap:
    for path in [f"/v2/sandboxes/{NAME}/restore?teamId={TEAM}&projectId={PROJ}",
                 f"/v2/sandboxes/{NAME}/snapshot?teamId={TEAM}&projectId={PROJ}"]:
        c, r = api("POST", path, {"snapshotId": snap})
        print(f"  POST {path.split('?')[0]} -> {c}: {r[:250]}", flush=True)
    c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
               {"projectId": PROJ, "name": NAME, "snapshotId": snap})
    print(f"  create+snapshotId -> {c}: {r[:300]}", flush=True)

# --- [D] cmd 参数面: environment / workingDirectory ---
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print(f"\n== [D] create -> {c}", flush=True)
sid = json.loads(r)["sandbox"]["currentSessionId"] if c == 200 else None
print("sid:", sid, flush=True)

if sid:
    tests = [
        ("env-only", {"command": "python3", "args": ["-c", "import os; print('ENV_FOO=', os.environ.get('FOO'))"],
                      "environment": {"FOO": "BAR123"}, "wait": True, "logs": True, "timeout": 300}),
        ("workdir", {"command": "python3", "args": ["-c", "import os; print('CWD=', os.getcwd())"],
                     "workingDirectory": "/tmp", "wait": True, "logs": True, "timeout": 300}),
        ("cmd-array", {"command": ["sh", "-c", "echo ARR=$0; id"], "wait": True, "logs": True, "timeout": 300}),
        ("cmd-object", {"command": {"path": "sh", "args": ["-c", "echo OBJ"]}, "wait": True, "logs": True, "timeout": 300}),
    ]
    for label, body in tests:
        c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
        print(f"  [{label}] status {c}: {r[:350]}", flush=True)
        time.sleep(1)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
