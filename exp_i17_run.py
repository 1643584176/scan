# I17 双沙箱运行流程: A 扫描 B
import json, base64, pathlib, urllib.request, urllib.error, time, re

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
        return e.code, e.read().decode()[:800]
    except Exception as e:
        return -1, f"EXC {type(e).__name__}: {e}"

def create_sandbox(name, policy_mode="deny-all"):
    api("DELETE", f"/v2/sandboxes/{name}?teamId={TEAM}&projectId={PROJ}")
    c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
               {"projectId": PROJ, "name": name, "networkPolicy": {"mode": policy_mode}})
    d = json.loads(r) if r.startswith("{") else {}
    sid = d.get("sandbox", {}).get("currentSessionId", "")
    print(f"  create {name}: {c} sid={sid}", flush=True)
    return sid

def exec_cmd(sid, script, timeout_ms=90000, env=None):
    payload = base64.b64encode(pathlib.Path(script).read_bytes()).decode()
    body = {"command": "python3", "args": ["-u", "-c", f"import base64;exec(base64.b64decode('{payload}').decode())"],
            "wait": True, "logs": True, "timeout": timeout_ms}
    if env:
        body["env"] = env
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body, timeout=timeout_ms//1000+60)
    out = []
    for line in r.splitlines():
        line = line.strip()
        if not line: continue
        try:
            d = json.loads(line)
            if d.get("stream") in ("stdout", "stderr"):
                out.append(d.get("data", ""))
            elif d.get("stream") == "command":
                out.append(f"\nEXIT: {d.get('command',{}).get('exitCode')}")
        except Exception:
            pass
    return c, "".join(out)

# 1. 创建 A(deny-all) 和 B(deny-all)
print("== 创建沙箱 ==", flush=True)
sid_b = create_sandbox("expi17b", "deny-all")
sid_a = create_sandbox("expi17a", "deny-all")

# 2. 获取 B 的 IP
print("== 获取 B 的 IP ==", flush=True)
c, out = exec_cmd(sid_b, "exp_i17.py" if False else "exp_i17_ip.py", 30000)
print(out, flush=True)
ip_b = ""
for m in re.finditer(r"本机IP: ([\d.]+)", out):
    ip_b = m.group(1)
print(f"B IP = {ip_b}", flush=True)

# 3. A 扫描 B
if ip_b:
    print("== A 扫描 B ==", flush=True)
    c, out = exec_cmd(sid_a, "exp_i17.py", 180000, env={"TARGET_IP": ip_b})
    print(out, flush=True)

# 4. 清理
time.sleep(1)
for n in ["expi17a", "expi17b"]:
    api("DELETE", f"/v2/sandboxes/{n}?teamId={TEAM}&projectId={PROJ}")
print("cleanup done", flush=True)
