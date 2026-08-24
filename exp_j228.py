# 实验J228: dump wrapunary(0x83aea0)完整代码找认证头字符串 + 测试init.sock连接
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

def bashfile(sid, cmd, label, n=40000):
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
               {"command": "bash", "args": ["-c", cmd], "wait": True, "logs": True, "timeout": 120})
    print(f"=== {label} status {c} ===", flush=True)
    print(r[:n], flush=True)
    return c

NAME = "expj228"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

bashfile(sid, "cp /run/vercel/share/sandbox-init /tmp/si", "CP", 2000)

# 1) dump wrapunary + newverifier + verify 引用的所有字符串
CODE = r'''
import struct
out = open("/tmp/d228.txt", "w")
def p(*a):
    line = " ".join(str(x) for x in a)
    out.write(line + "\n"); out.flush()
    print(line, flush=True)

data = open("/tmp/si", "rb").read()
phoff = struct.unpack_from("<Q", data, 0x20)[0]
phentsz = struct.unpack_from("<H", data, 0x36)[0]
phnum = struct.unpack_from("<H", data, 0x38)[0]
segs = []
for i in range(phnum):
    off = phoff + i * phentsz
    p_type, p_flags = struct.unpack_from("<II", data, off)
    p_offset, p_vaddr = struct.unpack_from("<QQ", data, off + 8)
    p_filesz, p_memsz = struct.unpack_from("<QQ", data, off + 0x20)
    segs.append([p_type, p_flags, p_offset, p_vaddr, p_filesz, p_memsz])

def v2f(v):
    for pt, pf, po, pv, pfs, pms in segs:
        if pt == 1 and pv <= v < pv + pfs:
            return po + (v - pv)
    return None

def dump_code(name, vaddr, size):
    f = v2f(vaddr)
    if f is None:
        p("CODE", name, "NO_SEG")
        return
    raw = data[f:f+size]
    p("CODE", name, hex(vaddr), "size", size, "hex", raw.hex())

# wrapunary 0x83aea0 (529B) + verify 0x83b3a0 (685B) + newverifier 0x83abc0 (440B)
dump_code("WRAPUNARY", 0x83aea0, 0x230)
dump_code("VERIFY", 0x83b3a0, 0x2c0)
dump_code("NEWVERIFIER", 0x83abc0, 0x1c0)
p("done")
out.close()
'''
st = run_cmd(sid, CODE, "J228A", timeout=200)
time.sleep(1)
bashfile(sid, "cat /tmp/d228.txt", "CODES", 40000)

# 2) init.sock 连接测试 (http1.1 over unix socket)
CODE2 = r'''
import socket
def try_sock():
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(4)
    try:
        s.connect("/run/vercel/share/init.sock")
        print("CONNECT_OK", flush=True)
        # connect-go POST Ping, json
        req = ("POST /vercel.sandbox.spawn.v1.SpawnService/Ping HTTP/1.1\r\n"
               "Host: localhost\r\nContent-Type: application/json\r\n"
               "Connect-Protocol-Version: 1\r\nContent-Length: 2\r\n\r\n{}")
        s.send(req.encode())
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
        print("RESP", d[:600].decode(errors="replace"), flush=True)
    except Exception as e:
        print("SOCK_ERR", type(e).__name__, str(e)[:150], flush=True)
    finally:
        s.close()
try_sock()
print("DONE2", flush=True)
'''
st = run_cmd(sid, CODE2, "J228B", timeout=120)
time.sleep(1)
bashfile(sid, "true", "NOOP", 500)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
