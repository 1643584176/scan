# 实验J93: 宿主 socket 暴露验证 — containerd/cell/metrics/apm + TCP 30001/30002/23456
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

NAME = "expj93"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

PROBE = r"""
import os, socket, stat

print("== [1] 宿主 socket 文件权限 ==", flush=True)
for p in ["/proc/1/root/run/containerd/containerd.sock",
          "/proc/1/root/run/containerd/containerd.sock.ttrpc",
          "/proc/1/root/run/cell/cell.sock",
          "/proc/1/root/run/metrics/metrics.sock",
          "/proc/1/root/run/apm/apm.sock"]:
    try:
        st = os.stat(p)
        print(f"  {p}: mode={oct(st.st_mode)} uid={st.st_uid} gid={st.st_gid}", flush=True)
    except Exception as e:
        print(f"  {p}: ERR {e}", flush=True)

print("== [2] unix socket connect 测试 ==", flush=True)
def try_unix(path, label, send=b"", timeout=4):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect(path)
        if send:
            s.sendall(send)
        data = b""
        try:
            data = s.recv(512)
        except socket.timeout:
            pass
        s.close()
        return f"CONNECT-OK resp={data[:100]!r}"
    except PermissionError:
        return "DENIED(permission)"
    except ConnectionRefusedError:
        return "REFUSED"
    except FileNotFoundError:
        return "NOFILE"
    except OSError as e:
        return f"ERR({e.errno} {e})"

for p in ["/proc/1/root/run/containerd/containerd.sock",
          "/proc/1/root/run/containerd/containerd.sock.ttrpc",
          "/proc/1/root/run/cell/cell.sock",
          "/proc/1/root/run/metrics/metrics.sock",
          "/proc/1/root/run/apm/apm.sock"]:
    print(f"  {p} -> {try_unix(p, 'unix')}", flush=True)

print("== [3] TCP 服务探测 ==", flush=True)
def try_tcp(port, label, timeout=4):
    try:
        s = socket.create_connection(("127.0.0.1", port), timeout=timeout)
        s.settimeout(timeout)
        data = b""
        try:
            data = s.recv(512)
        except socket.timeout:
            pass
        s.close()
        return f"OPEN banner={data[:100]!r}"
    except (ConnectionRefusedError, socket.timeout, OSError) as e:
        return f"CLOSED/ERR({e})"

for port in [30001, 30002, 23456]:
    print(f"  127.0.0.1:{port} -> {try_tcp(port, 'tcp')}", flush=True)

print("== [4] sandbox-init 二进制 strings 抽查 (敏感串) ==", flush=True)
import subprocess
out = subprocess.run(["strings", "/proc/1/root/run/vercel/share/sandbox-init"],
                     capture_output=True, text=True, timeout=60)
if out.returncode != 0:
    print("  strings not available, try grep", flush=True)
else:
    hits = [l for l in out.stdout.splitlines() if any(
        k in l for k in ["token", "secret", "api.vercel", "http://", "https://",
                         "signature", "PUBKEY", "SOCKET", "spawn", "cell", "containerd",
                         "metric", "apm", "grpc", "unix:/"])]
    print(f"  total lines={len(out.stdout.splitlines())} hits={len(hits)}", flush=True)
    for h in hits[:60]:
        print("   ", h[:150], flush=True)
"""
run_cmd(sid, PROBE, "host-sock", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
