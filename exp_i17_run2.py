# I17-2 策略组合矩阵: 双沙箱策略交叉测试横向可达性
# 组合1: A=allow-all, B=deny-all   -> B 入站是否受 deny-all 保护?
# 组合2: A=allow-all, B=allow-all  -> 双 allow(默认?) 沙箱间是否隔离?
# 组合3: A=deny-all,  B=allow-all  -> A 出站 deny 是否阻断横向?
# 组合4: A=deny-all,  B=deny-all   -> 双 deny(对照组)
import json, base64, pathlib, urllib.request, urllib.error, time, re, sys

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

def create_sandbox(name, mode):
    api("DELETE", f"/v2/sandboxes/{name}?teamId={TEAM}&projectId={PROJ}")
    c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
               {"projectId": PROJ, "name": name, "networkPolicy": {"mode": mode}})
    d = json.loads(r) if r.startswith("{") else {}
    sid = d.get("sandbox", {}).get("currentSessionId", "")
    print(f"  create {name} ({mode}): {c} sid={sid}", flush=True)
    return sid

def update_policy(sid, mode):
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/network-policy?teamId={TEAM}", {"mode": mode})
    print(f"  update policy -> {mode}: {c} {r[:100]}", flush=True)
    time.sleep(2)
    return c

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
        if not line:
            continue
        try:
            d = json.loads(line)
            if d.get("stream") in ("stdout", "stderr"):
                out.append(d.get("data", ""))
            elif d.get("stream") == "command":
                out.append(f"\nEXIT: {d.get('command',{}).get('exitCode')}")
        except Exception:
            pass
    return c, "".join(out)

# 1. 创建 B(deny-all) + A(allow-all)
print("== 创建沙箱 ==", flush=True)
sid_b = create_sandbox("expi17b", "deny-all")
sid_a = create_sandbox("expi17a", "allow-all")

# 2. 获取 B 的 IP
print("== 获取 B 的 IP ==", flush=True)
c, out = exec_cmd(sid_b, "exp_i17_ip.py", 30000)
print(out, flush=True)
ip_b = ""
for m in re.finditer(r"本机IP: ([\d.]+)", out):
    ip_b = m.group(1)
print(f"B IP = {ip_b}", flush=True)

if not ip_b:
    print("!! 无法获取 B 的 IP, 中止", flush=True)
    sys.exit(1)

# 3. 组合1: A=allow-all -> B=deny-all
print("\n== 组合1: A=allow-all, B=deny-all ==", flush=True)
c, out = exec_cmd(sid_a, "exp_i17_scan2.py", 120000, env={"TARGET_IP": ip_b})
print(out, flush=True)

# 4. 组合2: B -> allow-all
print("\n== 组合2: A=allow-all, B=allow-all ==", flush=True)
update_policy(sid_b, "allow-all")
c, out = exec_cmd(sid_a, "exp_i17_scan2.py", 120000, env={"TARGET_IP": ip_b})
print(out, flush=True)

# 5. 组合3: A -> deny-all
print("\n== 组合3: A=deny-all, B=allow-all ==", flush=True)
update_policy(sid_a, "deny-all")
c, out = exec_cmd(sid_a, "exp_i17_scan2.py", 120000, env={"TARGET_IP": ip_b})
print(out, flush=True)

# 6. 组合4: B -> deny-all
print("\n== 组合4: A=deny-all, B=deny-all ==", flush=True)
update_policy(sid_b, "deny-all")
c, out = exec_cmd(sid_a, "exp_i17_scan2.py", 120000, env={"TARGET_IP": ip_b})
print(out, flush=True)

# 7. 清理
time.sleep(1)
for n in ["expi17a", "expi17b"]:
    api("DELETE", f"/v2/sandboxes/{n}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
