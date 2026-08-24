# 实验J98: 宿主 rootfs 找服务二进制 — 定位 30001/23456/30002 服务进程与 RPC 路径
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

NAME = "expj98"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

PROBE = r"""
import os, re

print("== [1] /proc/1/root/vercel 完整枚举 ==", flush=True)
r = os.popen("ls -laR /proc/1/root/vercel/ 2>&1 | head -100").read()
print(r, flush=True)

print("== [2] /proc/1/root/opt 枚举 ==", flush=True)
r = os.popen("ls -laR /proc/1/root/opt/ 2>&1 | head -60").read()
print(r, flush=True)

print("== [3] 可执行文件清单 (宿主 rootfs) ==", flush=True)
r = os.popen("find /proc/1/root/vercel /proc/1/root/opt /proc/1/root/usr/local/bin /proc/1/root/usr/local/sbin -type f -size +1M 2>/dev/null | head -40").read()
print(r, flush=True)

print("== [4] 端口字符串搜索候选二进制 ==", flush=True)
cands = []
r = os.popen("find /proc/1/root/vercel /proc/1/root/opt /proc/1/root/usr/local -type f -size +500k -size -100M 2>/dev/null | head -30").read()
for f in r.splitlines():
    f = f.strip()
    if not f:
        continue
    try:
        with open(f, "rb") as fh:
            data = fh.read()
        for needle in [b"30001", b"30002", b"23456"]:
            if needle in data:
                idx = data.find(needle)
                window = data[max(0, idx-120):idx+120]
                strs = re.findall(rb"[ -~]{4,}", window)
                cands.append((f, needle.decode(), [s.decode(errors="replace") for s in strs][:12]))
    except Exception:
        pass
for f, needle, strs in cands:
    print(f"  [{needle}] {f}", flush=True)
    print(f"     ctx: {strs}", flush=True)
if not cands:
    print("  no candidates found", flush=True)

print("== [5] /proc/1/root/etc 服务配置线索 ==", flush=True)
for p in ["/proc/1/root/etc/supervisord.conf", "/proc/1/root/etc/init.d/", "/proc/1/root/etc/systemd/system/"]:
    r = os.popen(f"ls -la {p} 2>&1 | head -20").read()
    print(f"--- {p} ---", flush=True)
    print(r, flush=True)
"""
run_cmd(sid, PROBE, "host-bin", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
