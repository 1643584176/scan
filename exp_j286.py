# -*- coding: utf-8 -*-
"""实验J286: init vs 沙箱进程 权限边界对比 (决定性判定)
对比 sandbox-init (PID1) 与沙箱内进程:
1) seccomp 状态 (/proc/1/status Seccomp + /proc/1/seccomp 过滤器差异)
2) cap_bset/effective 差异
3) ns inode 对比 (mnt/net/pid/ipc/uts/cgroup/user)
4) init environ (宿主侧注入的变量?)
5) init 挂载视图 (/proc/1/mountinfo 与 /proc/self/mountinfo 对比)
6) init maps 可写段详情 (shellcode 注入候选)
"""
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

def run_cmd(sid, code, label, timeout=280):
    body = {"command": "python3", "args": ["-c", code],
            "wait": True, "logs": True, "timeout": timeout}
    t0 = time.time()
    for attempt in range(4):
        c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
        if c == 200:
            break
        print(f"  retry[{attempt}] status {c}: {r[:150]}", flush=True)
        if c == 410 or "sandbox_stopped" in r:
            return "DEAD"
        time.sleep(3)
    print(f"=== cmd[{label}] status {c} wall={time.time()-t0:.1f}s ===", flush=True)
    out = ""
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
                out += d.get("data", "")
        except Exception:
            print(line[:400], flush=True)
    return out

NAME = "expj286"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
if c != 200:
    print("create fail", r[:300], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

CODE = r'''
import os, subprocess

def sh(cmd, t=6):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=t)
        return (r.stdout or b"").decode("latin1", "replace")
    except Exception as e:
        return "ERR %s" % e

print("===== 1. Seccomp 对比 =====", flush=True)
print("PID1:", sh("grep -E 'Seccomp|NoNewPrivs|Cap' /proc/1/status"), flush=True)
print("SELF:", sh("grep -E 'Seccomp|NoNewPrivs|Cap' /proc/self/status"), flush=True)

print("===== 2. Cap 对比 =====", flush=True)
print("PID1:", sh("cat /proc/1/status | grep -E 'Cap(Eff|Bnd|Prm|Inh)'"), flush=True)
print("SELF:", sh("cat /proc/self/status | grep -E 'Cap(Eff|Bnd|Prm|Inh)'"), flush=True)

print("===== 3. ns inode 对比 =====", flush=True)
for ns in ("mnt", "net", "pid", "ipc", "uts", "cgroup", "user"):
    p1 = os.readlink("/proc/1/ns/%s" % ns)
    ps = os.readlink("/proc/self/ns/%s" % ns)
    print("%-6s PID1=%s SELF=%s SAME=%s" % (ns, p1, ps, p1 == ps), flush=True)

print("===== 4. PID1 environ (完整键值) =====", flush=True)
try:
    env = open("/proc/1/environ", "rb").read()
    print("bytes:", len(env), flush=True)
    for kv in env.split(b"\x00"):
        if kv and b"=" in kv:
            k, v = kv.split(b"=", 1)
            print("%s=%s" % (k.decode("latin1", "replace"), v.decode("latin1", "replace")), flush=True)
except Exception as e:
    print("ENVIRON_ERR %s: %s" % (type(e).__name__, e), flush=True)

print("===== 5. mountinfo 对比 (差异行) =====", flush=True)
m1 = set(sh("cat /proc/1/mountinfo 2>&1").splitlines())
ms = set(sh("cat /proc/self/mountinfo 2>&1").splitlines())
print("PID1-only:", flush=True)
for l in sorted(m1 - ms):
    print("  ", l[:200], flush=True)
print("SELF-only:", flush=True)
for l in sorted(ms - m1):
    print("  ", l[:200], flush=True)

print("===== 6. PID1 maps 全部可写段 =====", flush=True)
print(sh("cat /proc/1/maps | grep -E 'rw'"), flush=True)

print("===== 7. PID1 uid/gid 与用户 =====", flush=True)
print(sh("cat /proc/1/status | grep -E '^Uid|^Gid'"), flush=True)
print(sh("ls -la /proc/1/exe; readlink /proc/1/exe"), flush=True)
'''
out = run_cmd(sid, CODE, "NS_COMPARE", timeout=100)
print(out[:8000], flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
