# 实验J9驱动: 三次 cmd 流程 - 启动strace -> 触发agent请求 -> dump日志
import json, base64, pathlib, time, urllib.request, urllib.error

TOKEN = "vcp_REDACTED_PLACEHOLDER"
TEAM = "team_GIy1SZ444lspqeNbh4r8uAUg"
PROJ = "prj_iyw2xfjP3RKPT7n8b8c1tBIxxK5F"

def api(method, path, body=None, timeout=120):
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

def run_cmd(sid, script_mode, label):
    payload = base64.b64encode(pathlib.Path("exp_j9.py").read_bytes()).decode()
    code = f"import base64,sys;sys.argv=['x','{script_mode}'];exec(base64.b64decode('{payload}').decode())"
    body = {"command": "python3", "args": ["-c", code],
            "wait": True, "logs": True, "timeout": 60000}
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
    print(f"=== cmd[{label}] status {c} ===", flush=True)
    for line in r.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
            if d.get("stream") in ("stdout", "stderr"):
                print(d.get("data", ""), end="", flush=True)
            elif d.get("stream") == "command":
                print("\nEXIT:", d.get("command", {}).get("exitCode"), flush=True)
        except Exception:
            print(line[:400], flush=True)

NAME = "expj9"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

# 1. 检查工具 + 启动 strace
run_cmd(sid, "check", "check")
run_cmd(sid, "capture", "capture")
print(">>> sleep 3 等 strace attach 完成", flush=True)
time.sleep(3)
# 2. 触发 agent 活动: 发一个 cmd(agent 必须向 init.sock 发带签名 Spawn 请求)
run_cmd(sid, "noop", "trigger")
# 3. dump 日志
run_cmd(sid, "dump", "dump")

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
