# 实验J112: 快照继承面 — 同 project 新沙箱是否恢复旧沙箱磁盘(自动快照恢复路径)
# 动机: j103/105 确认停止时自动生成快照(currentSnapshotId), 但恢复路径从未验证;
#       若新沙箱继承最近快照磁盘 => 跨沙箱持久化/数据面
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

def create(name, extra=None):
    api("DELETE", f"/v2/sandboxes/{name}?teamId={TEAM}&projectId={PROJ}")
    body = {"projectId": PROJ, "name": name,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}}
    if extra:
        body.update(extra)
    c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}", body)
    print(f"create {name}: {c}", flush=True)
    if c != 200:
        print(f"  RAW: {r[:300]}", flush=True)
        return None, r
    return json.loads(r)["sandbox"]["currentSessionId"], json.loads(r)

def sandbox_status(name):
    c, r = api("GET", f"/v2/sandboxes?teamId={TEAM}&projectId={PROJ}")
    if c != 200:
        return None
    for s in json.loads(r)["sandboxes"]:
        if s["name"] == name:
            return s
    return None

def wait_stopped(name, timeout_s=150):
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        s = sandbox_status(name)
        if s and s.get("status") == "stopped":
            return s
        time.sleep(3)
    return sandbox_status(name)

MARKER = "J112_MARKER_0820"

WRITE_PROBE = r"""
import os
markers = {
    "/vercel/sandbox/j112_marker.txt": "__MARKER__",
    "/tmp/j112_tmp_marker.txt": "__MARKER__",
    "/home/vercel-sandbox/j112_home_marker.txt": "__MARKER__",
    "/j112_root_marker.txt": "__MARKER__",
}
for p, content in markers.items():
    try:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as f:
            f.write(content)
        print("WRITE OK %s" % p, flush=True)
    except Exception as e:
        print("WRITE FAIL %s: %s" % (p, e), flush=True)
print("WRITE_DONE", flush=True)
""".replace("__MARKER__", MARKER)

CHECK_PROBE = r"""
import os
paths = ["/vercel/sandbox/j112_marker.txt", "/tmp/j112_tmp_marker.txt",
         "/home/vercel-sandbox/j112_home_marker.txt", "/j112_root_marker.txt"]
for p in paths:
    try:
        data = open(p).read().strip()
        print("FOUND %s -> %s" % (p, data), flush=True)
    except Exception as e:
        print("MISS  %s" % p, flush=True)
print("CHECK_DONE", flush=True)
"""

print("################ [A] 沙箱A: 写标记 + timeout=10000 快速停止 ################", flush=True)
SID_A, _ = create("expj112a", {"timeout": 10000})
if SID_A:
    run_cmd(SID_A, WRITE_PROBE, "A-write-marker")
    print(">> 等待 A 自动停止 (timeout=10s)...", flush=True)
    st = wait_stopped("expj112a", timeout_s=90)
    print("A status:", json.dumps(st, ensure_ascii=False)[:400] if st else "None", flush=True)
    snap_a = (st or {}).get("currentSnapshotId")
    print("A currentSnapshotId:", snap_a, flush=True)

print("\n################ [B] 新沙箱B: 检查标记(继承快照?) ################", flush=True)
SID_B, _ = create("expj112b")
if SID_B:
    run_cmd(SID_B, CHECK_PROBE, "B-check-marker")

print("\n################ [C] 对照: persistent=false 沙箱C ################", flush=True)
SID_C, _ = create("expj112c", {"persistent": False})
if SID_C:
    run_cmd(SID_C, CHECK_PROBE, "C-check-marker")

print("\n################ [D] 端点变体: start/restart/wake ################", flush=True)
for ep in ["start", "restart", "wake", "resume", "stop", "reboot", "startSession"]:
    c, r = api("POST", f"/v2/sandboxes/expj112b/{ep}?teamId={TEAM}&projectId={PROJ}")
    print(f"  POST {ep}: {c}: {r[:150]}", flush=True)

print("\n################ [E] name 复用: DELETE B 后重建同名 ################", flush=True)
if SID_B:
    c, r = api("DELETE", f"/v2/sandboxes/expj112b?teamId={TEAM}&projectId={PROJ}")
    print("DELETE B:", c, flush=True)
    SID_B2, _ = create("expj112b")
    if SID_B2:
        run_cmd(SID_B2, CHECK_PROBE, "B2-check-marker(name-reuse)")

# cleanup
for name in ["expj112a", "expj112b", "expj112c"]:
    c, r = api("DELETE", f"/v2/sandboxes/{name}?teamId={TEAM}&projectId={PROJ}")
    print(f"cleanup {name}: {c}", flush=True)
print("\ncleanup done", flush=True)
