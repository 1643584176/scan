# 实验J92: /proc/net 直接解析监听端口 + 网络拓扑 + interactivePort 侧写
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

NAME = "expj92"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

PROBE = r"""
import os, struct, socket

def parse_proc_net(path):
    out = []
    try:
        with open(path) as f:
            lines = f.readlines()[1:]
        for ln in lines:
            parts = ln.split()
            if len(parts) < 4:
                continue
            st = parts[3]
            if st != "0A":  # LISTEN
                continue
            laddr, lport = parts[1].split(":")
            out.append((laddr, int(lport, 16), parts[9] if len(parts) > 9 else ""))
    except Exception as e:
        return [("ERR", str(e))]
    return out

print("== [1] TCP LISTEN (共享 net ns) ==", flush=True)
for addr, port, inode in parse_proc_net("/proc/net/tcp"):
    print(f"  tcp  {addr}:{port} inode={inode}", flush=True)
for addr, port, inode in parse_proc_net("/proc/net/tcp6"):
    print(f"  tcp6 {addr}:{port} inode={inode}", flush=True)

print("== [2] UDP bind ==", flush=True)
try:
    with open("/proc/net/udp") as f:
        lines = f.readlines()[1:]
    for ln in lines:
        parts = ln.split()
        if len(parts) < 4:
            continue
        laddr, lport = parts[1].split(":")
        print(f"  udp {laddr}:{int(lport,16)}", flush=True)
except Exception as e:
    print("  ERR", e, flush=True)

print("== [3] unix socket 数 ==", flush=True)
try:
    with open("/proc/net/unix") as f:
        lines = f.readlines()
    print(f"  total unix sockets: {len(lines)-1}", flush=True)
    for ln in lines[1:100]:
        parts = ln.split()
        if len(parts) >= 8 and parts[7]:
            print("  ", parts[7], flush=True)
except Exception as e:
    print("  ERR", e, flush=True)

print("== [4] 网络拓扑 ==", flush=True)
for cmd in [["ip", "addr"], ["ip", "route"], ["cat", "/etc/resolv.conf"]]:
    try:
        r = os.popen(" ".join(cmd) + " 2>&1").read()
        print(f"--- {' '.join(cmd)} ---", flush=True)
        print(r[:1500], flush=True)
    except Exception as e:
        print("ERR", e, flush=True)

print("== [5] /proc/1/root/run 目录 ==", flush=True)
r = os.popen("ls -la /proc/1/root/run/ 2>&1; echo ---; ls -la /proc/1/root/run/vercel/share/ 2>&1").read()
print(r[:1500], flush=True)

print("== [6] /proc/1/root 顶层 ==", flush=True)
r = os.popen("ls -la /proc/1/root/ 2>&1 | head -30").read()
print(r[:1500], flush=True)
"""
run_cmd(sid, PROBE, "net-proc", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
