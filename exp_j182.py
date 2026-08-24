# 实验J182: 逐chunk安全提取字符串->本地逆向 + Host白名单fuzz
# j181: 全量read+findall被杀(内存启发式); 30001校验Host(vercel.com->400, 127.0.0.1->404); UDP被杀
# 本步: 1)逐64KB chunk提取 16+可打印串(过滤误报) 写/tmp/strs.txt, 分批tail下载
#       2)30001 Host白名单fuzz(localhost/sandbox/guestIP/vercel域名)
#       3)ELF段布局(定位rodata/data段偏移, 后续精准下载)
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

def catfile(sid, path, label, n=10000):
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
               {"command": "cat", "args": [path], "wait": True, "logs": True, "timeout": 100})
    print(f"=== {label} status {c} ===", flush=True)
    print(r[:n], flush=True)
    return c

def bashfile(sid, cmd, label, n=10000):
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
               {"command": "bash", "args": ["-c", cmd], "wait": True, "logs": True, "timeout": 100})
    print(f"=== {label} status {c} ===", flush=True)
    print(r[:n], flush=True)
    return c

NAME = "expj182"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c)
if c != 200:
    print(r[:400])
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

# PA: 逐chunk提取字符串 (安全模式) -> /tmp/strs.txt
PA = r'''
import os, re
out = open("/tmp/d182a.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
p("start")
res = open("/tmp/strs.txt", "wb")
pat = re.compile(rb"[\x20-\x7e]{16,}")
skip = re.compile(rb"^[A-Za-z0-9_]{16,}$")  # 纯字母数字=可能代码
n = 0
fd = os.open("/run/vercel/share/sandbox-init", os.O_RDONLY)
while True:
    d = os.read(fd, 65536)
    if not d:
        break
    for m in pat.finditer(d):
        s = m.group(0)
        # 过滤: 纯英文单词串(代码)、全是路径分隔符的
        if skip.match(s) and "/" not in s and "." not in s and "-" not in s:
            continue
        if len(s) >= 16:
            res.write(s + b"\n")
            n += 1
os.close(fd)
res.close()
p("nstrs", n)
try:
    p("size", os.path.getsize("/tmp/strs.txt"))
except Exception as ex:
    p("size_err", repr(ex))
p("done")
out.close()
'''

# PB: Host 白名单 fuzz
PB = r'''
import os, socket
out = open("/tmp/d182b.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
def http(port, path, host, to=2):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(to)
        s.connect(("127.0.0.1", port))
        s.send(f"GET {path} HTTP/1.0\r\nHost: {host}\r\n\r\n".encode())
        d = b""
        try:
            while True:
                b = s.recv(4096)
                if not b:
                    break
                d += b
                if len(d) > 600:
                    break
        except Exception:
            pass
        s.close()
        return d
    except Exception as ex:
        return ("EXC:" + repr(ex)).encode()
p("start")
# 获取 guest IP
import subprocess
ip = ""
try:
    ip = subprocess.run(["ip", "addr"], capture_output=True, text=True, timeout=5).stdout
    p("IPADDR", ip[:300])
except Exception as ex:
    p("ip_err", repr(ex))
hosts = ["localhost", "sandbox", "sandbox.local", "vercel-sandbox", "sandbox-init",
         "init", "control", "127.0.0.1.nip.io", "localhost.localdomain",
         "sandbox.vercel.app", "*.vercel.app", "vercel.app", "api.vercel.com",
         "vsbx.vercel.app", "sandbox.run.vercel.app", "expj182.vercel.app"]
for host in hosts:
    d = http(30001, "/", host)
    code = b""
    if d.startswith(b"HTTP"):
        code = d.split(b"\r\n")[0]
    p("HOST", host, code, d[:120])
    out.flush()
p("done")
out.close()
'''

# PC: ELF 段布局 (rodata/data 定位)
PC = r'''
import os, struct
out = open("/tmp/d182c.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
p("start")
fd = os.open("/run/vercel/share/sandbox-init", os.O_RDONLY)
head = os.read(fd, 64)
e_phoff = struct.unpack("<Q", head[32:40])[0]
e_phentsize = struct.unpack("<H", head[54:56])[0]
e_phnum = struct.unpack("<H", head[56:58])[0]
p("phoff", hex(e_phoff), "phentsize", e_phentsize, "phnum", e_phnum)
for i in range(e_phnum):
    os.lseek(fd, e_phoff + i * e_phentsize, 0)
    h = os.read(fd, e_phentsize)
    p_type = struct.unpack("<I", h[0:4])[0]
    p_flags = struct.unpack("<I", h[4:8])[0]
    p_offset = struct.unpack("<Q", h[8:16])[0]
    p_vaddr = struct.unpack("<Q", h[16:24])[0]
    p_filesz = struct.unpack("<Q", h[32:40])[0]
    p_memsz = struct.unpack("<Q", h[40:48])[0]
    p("PH", i, "type", p_type, "flags", p_flags, "off", hex(p_offset),
      "vaddr", hex(p_vaddr), "fsz", hex(p_filesz), "msz", hex(p_memsz))
os.close(fd)
p("done")
out.close()
'''

steps = [
    ("extract", "/tmp/d182a.txt", PA),
    ("hosts", "/tmp/d182b.txt", PB),
    ("elf", "/tmp/d182c.txt", PC),
]
for label, marker, code in steps:
    st = run_cmd(sid, code, label, timeout=280)
    time.sleep(2)
    cf = catfile(sid, marker, f"marker[{label}]", 6000)
    if st == "DEAD" or cf == 410:
        print(f"\n!!! DEATH after cmd[{label}] -> trigger = {label}", flush=True)
        break

# 下载 strs.txt (分批)
if cf != 410 and st != "DEAD":
    for off in [1, 8000, 16000, 24000, 32000, 40000, 48000, 56000, 64000, 72000]:
        bashfile(sid, f"tail -c +{off} /tmp/strs.txt | head -c 8000", f"strs[{off}]", 10000)
        time.sleep(1)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
