# 实验J109: init.sock 非RPC路径(pprof/metrics) + 30001/23456 完整方法字典 + interactivePort 入站面
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

# --- [A] /v1/sandboxes 完整响应找 URL/入站地址字段 ---
print("== [A] /v1/sandboxes 完整字段 ==", flush=True)
c, r = api("GET", f"/v1/sandboxes?teamId={TEAM}&project={PROJ}")
try:
    sbx = json.loads(r)["sandboxes"][0]
    print(f"  keys: {sorted(sbx.keys())}", flush=True)
    print(f"  {json.dumps(sbx)[:600]}", flush=True)
except Exception as e:
    print(f"  {r[:300]}", flush=True)

NAME = "expj109"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("\ncreate:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

PROBE = r"""
import subprocess, time

def sh(cmd, timeout=8):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=timeout)
        return (r.stdout + r.stderr).decode(errors="replace").strip()[:400]
    except Exception as e:
        return f"EXC({e})"

def curl_sock(path, method="GET"):
    cmd = ["curl", "-sS", "-m", "6", "-i", "-X", method,
           "--unix-socket", "/run/vercel/share/init.sock",
           "-H", "Content-Type: application/connect+json",
           "-H", "Connect-Protocol-Version: 1",
           "-H", "x-timestamp: " + str(int(time.time() * 1000)),
           "http://localhost" + path]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=10)
        return (r.stdout + r.stderr).decode(errors="replace")[:250].replace("\r\n", " | ")
    except Exception as e:
        return f"EXC({e})"

print("== [B1] init.sock 非 RPC 路径 ==", flush=True)
for p in ["/debug/pprof/", "/debug/pprof/goroutine?debug=1", "/debug/pprof/heap",
          "/debug/vars", "/metrics", "/healthz", "/health", "/readyz", "/debug/requests",
          "/vercel.sandbox.spawn.v1.SpawnService/Spawn?debug=1", "/favicon.ico"]:
    print(f"  GET {p[:50]} -> {curl_sock(p)}", flush=True)

print("== [B2] POST 变体 ==", flush=True)
for p in ["/debug/pprof/", "/metrics", "/healthz"]:
    print(f"  POST {p} -> {curl_sock(p, 'POST')}", flush=True)

print("== [B3] 沙箱内监听端口 (interactivePort 入站) ==", flush=True)
print(sh("ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null || cat /proc/net/tcp | head -20"), flush=True)

print("== [B4] interactivePort 自连测试 ==", flush=True)
print(sh("for p in 26661 3000 8080 80; do timeout 2 bash -c 'echo > /dev/tcp/127.0.0.1/'$p 2>/dev/null && echo port-$p-OPEN || echo port-$p-CLOSED; done"), flush=True)

print("== [B5] 30001/30002/23456 完整方法字典 ==", flush=True)
services = ["vercel.sandbox.spawn.v1.SpawnService",
            "vercel.cell.v1.CellService",
            "vercel.celld.v1.CelldService",
            "vercel.sandbox.v1.SandboxService",
            "vercel.runtime.v1.RuntimeService",
            "vercel.exec.v1.ExecService",
            "vercel.pty.v1.PtyService",
            "vercel.v1.VercelService",
            "vercel.bees.v1.BeesService",
            "vercel.node.v1.NodeService",
            "vercel.api.v1.ApiService",
            "vercel.internal.v1.InternalService",
            "cell.v1.CellService",
            "bees.cell.v1.CellService",
            "vercel.host.v1.HostService"]
methods = ["Ping","Kill","Spawn","Exec","List","Info","Status","Logs","Wait","Signal",
           "Start","Stop","Restart","Destroy","Cleanup","Get","SetEnv","GetEnv","Stat",
           "Write","Read","Open","Close","Version","Describe","Events","Stream","Attach",
           "Resize","Connect","Watch","Snapshot","Restore","Copy","Move","Update","Patch",
           "Health","HealthCheck","Register","Heartbeat"]
def probe_port(port, svc, m):
    path = "/%s/%s" % (svc, m)
    cmd = ["curl", "-sS", "-m", "3", "-o", "/dev/null", "-w", "%{http_code}",
           "-X", "POST", "http://127.0.0.1:%d" % port + path,
           "-H", "Content-Type: application/connect+json",
           "-H", "Connect-Protocol-Version: 1",
           "-H", "x-timestamp: " + str(int(time.time() * 1000)),
           "--data-binary", "@-"]
    try:
        r = subprocess.run(cmd, input=b"\x00\x00\x00\x00\x02{}", capture_output=True, timeout=6)
        return (r.stdout or r.stderr).decode(errors="replace").strip()
    except Exception as e:
        return "EXC"
hits = []
for port in [30001, 23456]:
    for svc in services:
        for m in methods:
            code = probe_port(port, svc, m)
            if code not in ("404", "000", "EXC", "403"):
                hits.append((port, svc, m, code))
                print(f"  HIT {port} /{svc}/{m} -> {code}", flush=True)
print(f"  dict done, hits={len(hits)}", flush=True)
for h in hits:
    print("  ", h, flush=True)
"""
run_cmd(sid, PROBE, "pprof-methods-inbound", wait=True, timeout=600000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
