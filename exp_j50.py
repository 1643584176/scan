# 实验J50: proto 服务/方法名提取 + Connect 协议调用
# 目标: 枚举 vercel.sandbox.* 服务, 用 HTTP/1.1+JSON 调 Connect API
import json, time, urllib.request, urllib.error, sys
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

def run_cmd(sid, code, label, wait=True, timeout=300):
    body = {"command": "python3", "args": ["-c", code],
            "wait": wait, "logs": True, "timeout": timeout}
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
    print(f"=== cmd[{label}] status {c} ===", flush=True)
    if c != 200:
        print(f"  RAW: {r[:400]}", flush=True)
        return
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

NAME = "expj50"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

SCAN = r'''
import os, re, subprocess, socket, json

print("===== [1] proto 服务名/方法名全提取 =====", flush=True)
b = open("/run/vercel/share/sandbox-init", "rb").read()
# 所有 vercel.sandbox 前缀串
for m in re.finditer(rb"vercel\.sandbox\.[a-zA-Z0-9_.]{3,80}", b):
    print("NS: %r" % m.group(0).decode('latin1'), flush=True)
# 所有 .proto 文件
protos = set()
for m in re.finditer(rb"[a-z0-9_/]{2,60}\.proto", b):
    protos.add(m.group(0).decode('latin1'))
print("--- proto files ---", flush=True)
for p in sorted(protos):
    print("PROTO: %s" % p, flush=True)
# Service 名
svcs = set()
for m in re.finditer(rb"\.(Spawn|Sandbox|Cell|Runtime|Agent|Control|Exec|File|Log|FS)[A-Za-z]*", b):
    svcs.add(m.group(1).decode('latin1'))
print("--- service-like ---", flush=True)
for s in sorted(svcs):
    print("SVC: %s" % s, flush=True)
# Request/Response 消息
msgs = set()
for m in re.finditer(rb"[A-Z][A-Za-z0-9]{2,40}(Request|Response|Reply)", b):
    msgs.add(m.group(0).decode('latin1'))
print("--- messages ---", flush=True)
for s in sorted(msgs)[:60]:
    print("MSG: %s" % s, flush=True)
# 方法路径格式 /pkg.Service/Method 的 Method 名
meths = set()
for m in re.finditer(rb"(?:Spawn|Sandbox|Cell|Runtime|Agent|Control|Exec|File|Log|FS)[A-Za-z]*/", b):
    pass
for m in re.finditer(rb"/([A-Z][A-Za-z0-9]{2,30})", b):
    meths.add(m.group(1).decode('latin1'))
print("--- method-like after / ---", flush=True)
for s in sorted(meths)[:60]:
    print("METH: %s" % s, flush=True)

print("===== [2] Connect JSON 调用 init.sock =====", flush=True)
def connect_call(path, body, port=None, unix=None, timeout=6):
    if unix:
        cmd = ["curl", "-sS", "--max-time", str(timeout), "-i", "-X", "POST",
               "--unix-socket", unix, "-H", "Content-Type: application/json",
               "-H", "Connect-Protocol-Version: 1", "-d", json.dumps(body),
               "http://localhost" + path]
    else:
        cmd = ["curl", "-sS", "--max-time", str(timeout), "-i", "-X", "POST",
               "-H", "Content-Type: application/json",
               "-H", "Connect-Protocol-Version: 1", "-d", json.dumps(body),
               "http://localhost:%d" % port + path]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout+2)
        return r.returncode, r.stdout[:800], r.stderr[:300]
    except Exception as e:
        return -1, "", str(e)

paths = [
    "/vercel.sandbox.spawn.v1.Spawn/Command",
    "/vercel.sandbox.spawn.v1.Spawn/Spawn",
    "/vercel.sandbox.spawn.v1.Spawn/Exec",
    "/vercel.sandbox.spawn.v1.Spawn/List",
    "/vercel.sandbox.spawn.v1.Spawn/Status",
    "/vercel.sandbox.spawn.v1.Spawn/Info",
    "/vercel.sandbox.spawn.v1.Spawn/Ping",
    "/vercel.sandbox.spawn.v1.SpawnService/Command",
    "/vercel.sandbox.spawn.v1.SpawnService/Spawn",
    "/vercel.sandbox.spawn.v1.Sandbox/Exec",
    "/vercel.sandbox.spawn.v1.Sandbox/Command",
    "/vercel.sandbox.v1.Sandbox/Exec",
    "/vercel.sandbox.v1.Sandbox/Command",
]
bodies = [
    {"command": "id"},
    {"command": "id", "arguments": [], "environment": {}},
    {},
    {"name": "test"},
]
for path in paths:
    for body in bodies[:2]:
        rc, out, err = connect_call(path, body, unix="/run/vercel/share/init.sock")
        # 只打印非 404 的
        if "404" not in out:
            print("PATH %s BODY %r -> RC=%d\n  %r\n  %r" % (path, body, rc, out, err), flush=True)
print("connect probes done", flush=True)

print("===== [3] Connect JSON 调用 23456/30001 =====", flush=True)
for port in [23456, 30001]:
    for path in paths[:6]:
        rc, out, err = connect_call(path, {"command": "id"}, port=port)
        if "404" not in out:
            print("PORT %d PATH %s -> RC=%d\n  %r\n  %r" % (port, path, rc, out, err), flush=True)
print("port probes done", flush=True)
'''
run_cmd(sid, SCAN, "connect-proto-enum", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
