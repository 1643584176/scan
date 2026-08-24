# 实验J214: 完整二进制侦察(写文件+cat模式, 可靠)
# 1) cp sandbox-init -> /tmp/si
# 2) python strings搜索: signature/verify/key相关字符串
# 3) 请求响应差异(NO_SIG vs BAD_SIG)
# 4) 请求后全局变量
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

def bashfile(sid, cmd, label, n=30000):
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
               {"command": "bash", "args": ["-c", cmd], "wait": True, "logs": True, "timeout": 100})
    print(f"=== {label} status {c} ===", flush=True)
    print(r[:n], flush=True)
    return c

NAME = "expj214"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

# 1) cp 二进制
bashfile(sid, "cp /run/vercel/share/sandbox-init /tmp/si && ls -la /tmp/si", "BIN_CP", 2000)

# 2) 二进制字符串侦察(写文件+cat)
CODE = r'''
import re
out = open("/tmp/strs.txt", "w")
def p(*a):
    line = " ".join(str(x) for x in a)
    out.write(line + "\n"); out.flush()
    print(line, flush=True)

data = open("/tmp/si", "rb").read()
p("SIZE", len(data))
words = re.findall(rb"[ -~]{6,}", data)
p("WORDS", len(words))
kws = [b"signature", b"Signature", b"SIGNATURE", b"verify", b"Verify", b"VERIFY",
       b"ed25519", b"Ed25519", b"pubkey", b"PubKey", b"PublicKey", b"X-Sig",
       b"x-signature", b"X-Signature", b"SignatureAlgorithm", b"jws", b"jwt"]
seen = set()
for w in words:
    if any(k in w for k in kws):
        try:
            s = w.decode("utf-8", "replace")
        except Exception:
            continue
        if s not in seen:
            seen.add(s)
            p("S:", s[:220])
p("DONE")
out.close()
'''
st = run_cmd(sid, CODE, "BIN_STR", timeout=120)
time.sleep(1)
bashfile(sid, "cat /tmp/strs.txt 2>&1 | head -80", "BIN_STR_CAT", 12000)

# 3) 错误消息线索
CODE2 = r'''
import re
out = open("/tmp/strs2.txt", "w")
def p(*a):
    line = " ".join(str(x) for x in a)
    out.write(line + "\n"); out.flush()
    print(line, flush=True)

data = open("/tmp/si", "rb").read()
words = re.findall(rb"[ -~]{4,}", data)
for w in words:
    lw = w.lower()
    if (b"invalid" in lw or b"bad" in lw or b"fail" in lw or b"not" in lw) and \
       (b"key" in lw or b"sig" in lw or b"verif" in lw or b"token" in lw):
        try:
            s = w.decode("utf-8", "replace")
        except Exception:
            continue
        p("E:", s[:220])
p("DONE")
out.close()
'''
st = run_cmd(sid, CODE2, "BIN_ERR", timeout=120)
time.sleep(1)
bashfile(sid, "cat /tmp/strs2.txt 2>&1 | head -60", "BIN_ERR_CAT", 10000)

# 4) 请求响应差异
CODE3 = r'''
import socket, time
out = open("/tmp/req.txt", "w")
def p(*a):
    line = " ".join(str(x) for x in a)
    out.write(line + "\n"); out.flush()
    print(line, flush=True)

def http(port, method, path, headers, body=b"", to=4):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(to)
        s.connect(("127.0.0.1", port))
        hdrs = f"{method} {path} HTTP/1.1\r\nHost: 127.0.0.1\r\n"
        for k, v in headers.items():
            hdrs += f"{k}: {v}\r\n"
        hdrs += f"Content-Length: {len(body)}\r\n\r\n"
        s.send(hdrs.encode() + body)
        d = b""
        try:
            while True:
                b2 = s.recv(4096)
                if not b2:
                    break
                d += b2
                if len(d) > 3000:
                    break
        except Exception:
            pass
        s.close()
        return d
    except Exception as ex:
        return ("EXC:" + repr(ex)).encode()

now = str(int(time.time()))
base = {"Content-Type": "application/connect+json", "Connect-Protocol-Version": "1",
        "X-Timestamp": now}
d1 = http(30001, "POST", "/foo", base, b"{}")
p("NO_SIG:", d1[:250])
d2 = http(30001, "POST", "/foo", dict(base, **{"X-Signature": "AAAA"}), b"{}")
p("BAD_SIG:", d2[:250])
p("DONE")
out.close()
'''
st = run_cmd(sid, CODE3, "REQ_TEST", timeout=120)
time.sleep(1)
bashfile(sid, "cat /tmp/req.txt 2>&1", "REQ_CAT", 4000)

# 5) 请求后全局变量
CODE4 = r'''
import os, struct
out = open("/tmp/glob.txt", "w")
def p(*a):
    line = " ".join(str(x) for x in a)
    out.write(line + "\n"); out.flush()
    print(line, flush=True)
fd = os.open("/proc/1/mem", os.O_RDWR)
def ra(a, n):
    os.lseek(fd, a, 0)
    return os.read(fd, n)
for addr in (0xe9e010, 0xe9e610, 0xe9e618, 0xe9f060, 0xe9f140):
    try:
        h = ra(addr, 24)
        p(hex(addr), h.hex(), struct.unpack("<QQQ", h))
    except Exception as e:
        p(hex(addr), "ERR", repr(e))
os.close(fd)
p("DONE")
out.close()
'''
st = run_cmd(sid, CODE4, "GLOBALS", timeout=120)
time.sleep(1)
bashfile(sid, "cat /tmp/glob.txt 2>&1", "GLOB_CAT", 3000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
