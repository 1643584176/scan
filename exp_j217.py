# 实验J217: 从二进制文件(非内存)分析 call 0x83abc0/0x83b3a0 调用点
# ELF解析text段file offset -> 搜E8 rel32 -> dump调用点上下文 -> 本地反汇编
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

NAME = "expj217"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

# 0) cp 二进制
bashfile(sid, "cp /run/vercel/share/sandbox-init /tmp/si && ls -la /tmp/si", "CP", 2000)

# 1) ELF解析 + 搜调用点
CODE = r'''
import struct
out = open("/tmp/d217.txt", "w")
def p(*a):
    line = " ".join(str(x) for x in a)
    out.write(line + "\n"); out.flush()
    print(line, flush=True)

data = open("/tmp/si", "rb").read()
p("SIZE", len(data))
# ELF64 header
assert data[:4] == b"\x7fELF", "not ELF"
phoff = struct.unpack_from("<Q", data, 0x20)[0]
phentsz = struct.unpack_from("<H", data, 0x36)[0]
phnum = struct.unpack_from("<H", data, 0x38)[0]
p("PH", phoff, phentsz, phnum)

# 找 LOAD 段
segments = []
for i in range(phnum):
    off = phoff + i * phentsz
    p_type, p_flags = struct.unpack_from("<II", data, off)
    p_offset, p_vaddr = struct.unpack_from("<QQ", data, off + 8)
    p_filesz, p_memsz = struct.unpack_from("<QQ", data, off + 0x20)
    segments.append((p_type, p_flags, p_offset, p_vaddr, p_filesz, p_memsz))
    p("SEG", i, "type", p_type, "flags", hex(p_flags), "off", hex(p_offset),
      "vaddr", hex(p_vaddr), "fsz", hex(p_filesz), "msz", hex(p_memsz))

# text段: LOAD + RX
rx = None
for s in segments:
    if s[0] == 1 and (s[1] & 5) == 5 and s[3] == 0x400000:
        rx = s
        break
p("RX", rx)
if not rx:
    p("NO_RX")
    p("done")
    out.close()
    raise SystemExit

_, _, foff, vaddr, fsz, _ = rx
v2f = lambda v: v - vaddr + foff
text_bytes = data[foff:foff + fsz]
p("TEXT_FILE", hex(foff), hex(fsz))

TARGETS = {0x83abc0: "newverifier", 0x83b3a0: "verify", 0x571700: "b64_alloc",
           0x83aea0: "wrapunary", 0x5f3a80: "VerifyWithOptions", 0x46e940: "f46e940",
           0x46f0c0: "f46f0c0"}
# 搜 call rel32
for i in range(len(text_bytes) - 5):
    if text_bytes[i] == 0xE8:
        rel = struct.unpack_from("<i", text_bytes, i + 1)[0]
        call_v = vaddr + i
        tgt = call_v + 5 + rel
        if tgt in TARGETS:
            p("CALL", TARGETS[tgt], hex(call_v))
            # dump 前0x90 后0x20
            s = max(0, i - 0x90)
            e = min(len(text_bytes), i + 5 + 0x20)
            p("CTX", hex(vaddr + s), text_bytes[s:e].hex())
p("done")
out.close()
'''
st = run_cmd(sid, CODE, "J217", timeout=200)
time.sleep(2)
bashfile(sid, "cat /tmp/d217.txt", "marker", 20000)
if st == "DEAD":
    print("\n!!! DEATH", flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
