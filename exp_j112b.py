# 实验J112b: 快照生成确认 + 继承验证(严谨版, timeout=60s)
# 目的: 确认 stopped 沙箱确实生成 currentSnapshotId; 快照内容=完整磁盘? 新沙箱是否继承
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

def list_sandboxes():
    c, r = api("GET", f"/v2/sandboxes?teamId={TEAM}&project={PROJ}")
    if c != 200:
        return c, r
    return c, json.loads(r)["sandboxes"]

def list_snapshots():
    c, r = api("GET", f"/v2/sandboxes/snapshots?teamId={TEAM}&project={PROJ}")
    if c != 200:
        return c, r
    return c, json.loads(r)["snapshots"]

MARKER = "J112B_MARKER_0820"

WRITE_PROBE = r"""
import os
markers = {
    "/vercel/sandbox/j112b_marker.txt": "__MARKER__",
    "/tmp/j112b_tmp_marker.txt": "__MARKER__",
    "/vercel/sandbox/j112b_big.bin": None,
}
for p, content in markers.items():
    try:
        if content is None:
            with open(p, "wb") as f:
                f.write(b"J" * (8 * 1024 * 1024))  # 8MB 大文件使快照 size 可观测
            print("WRITE OK %s (8MB)" % p, flush=True)
        else:
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
paths = ["/vercel/sandbox/j112b_marker.txt", "/tmp/j112b_tmp_marker.txt",
         "/vercel/sandbox/j112b_big.bin"]
for p in paths:
    try:
        data = open(p).read(64).strip()
        print("FOUND %s -> %r" % (p, data[:40]), flush=True)
    except Exception as e:
        print("MISS  %s" % p, flush=True)
print("CHECK_DONE", flush=True)
"""

NAME_A = "expj112ba"
api("DELETE", f"/v2/sandboxes/{NAME_A}?teamId={TEAM}&projectId={PROJ}")
print(">> 快照基线:", flush=True)
c, snaps0 = list_snapshots()
print(f"  snapshots before: {c} count={len(snaps0) if c==200 else '-'} raw={str(snaps0)[:200] if c!=200 else ''}", flush=True)
if c != 200:
    time.sleep(8)  # 可能限流, 等待后重试
    c, snaps0 = list_snapshots()
    print(f"  retry: {c} raw={str(snaps0)[:200]}", flush=True)

c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME_A, "timeout": 60000,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create A:", c, flush=True)
if c != 200:
    print(r[:300], flush=True)
    sys.exit(1)
SID_A = json.loads(r)["sandbox"]["currentSessionId"]
print("SID_A:", SID_A, flush=True)

run_cmd(SID_A, WRITE_PROBE, "A-write-marker")

print(">> 轮询 A 状态直至 stopped (最多 120s)...", flush=True)
st = None
for i in range(40):
    time.sleep(3)
    c, sbx = list_sandboxes()
    if c != 200:
        if i % 3 == 0:
            print(f"  list err {c}: {str(sbx)[:150]}", flush=True)
        continue
    match = [s for s in sbx if s["name"] == NAME_A]
    if match and match[0]["status"] == "stopped":
        st = match[0]
        break
    if i % 5 == 0:
        print(f"  poll[{i}] names={[s['name'] for s in sbx][:8]}", flush=True)
if st:
    print("A stopped. currentSnapshotId:", st.get("currentSnapshotId"), flush=True)
else:
    print("A NOT stopped in window; last list:", flush=True)
    c, sbx = list_sandboxes()
    print("  ", str(sbx)[:400] if c != 200 else [json.dumps(s, ensure_ascii=False)[:200] for s in sbx if s["name"] == NAME_A], flush=True)

c, snaps1 = list_snapshots()
print(f"snapshots after stop: {c} count={len(snaps1) if c==200 else '-'} raw={str(snaps1)[:200] if c!=200 else ''}", flush=True)
if c == 200:
    for s in snaps1[:3]:
        print("  ", json.dumps({k: s.get(k) for k in ("id", "sourceSessionId", "sizeBytes", "status", "expiresAt")}, ensure_ascii=False), flush=True)

print("\n>> 创建 B 检查继承...", flush=True)
NAME_B = "expj112bb"
api("DELETE", f"/v2/sandboxes/{NAME_B}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME_B,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create B:", c, flush=True)
if c == 200:
    SID_B = json.loads(r)["sandbox"]["currentSessionId"]
    run_cmd(SID_B, CHECK_PROBE, "B-check-inherit")

# 清理
for name in [NAME_A, NAME_B]:
    c, r = api("DELETE", f"/v2/sandboxes/{name}?teamId={TEAM}&projectId={PROJ}")
    print(f"cleanup {name}: {c}", flush=True)
c, snaps2 = list_snapshots()
print(f"snapshots after delete: {c} count={len(snaps2) if c==200 else '-'} raw={str(snaps2)[:200] if c!=200 else ''}", flush=True)
print("\ncleanup done", flush=True)
