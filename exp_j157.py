# 实验J157: PID1 environ/fd/网络连接 + gopclntab段边界修正解析
# j156: sandbox-init 是 connect-go SpawnService(Ping/Spawn/Kill/PTY), --pubkey=Ed25519验证命令签名
#       无vercel.com URL, 与宿主经cell.sock通信; gopclntab需从段边界0xa33100解析
# 方法: cmdA /proc/1/environ+/proc/1/fd+/proc/1/net/tcp 只读; cmdB 段边界gopclntab解析提取spawn/auth包函数
# 零破坏: 纯只读, 无连接无写入
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
        time.sleep(3)
    print(f"=== cmd[{label}] status {c} ===", flush=True)
    if c != 200:
        print(f"  RAW: {r[:400]}", flush=True)
        return ""
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

def catfile(sid, path, label, n=15000):
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
               {"command": "cat", "args": [path], "wait": True, "logs": True, "timeout": 100})
    print(f"=== {label} status {c} ===", flush=True)
    print(r[:n], flush=True)

NAME = "expj157"
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

# cmdA: PID1 environ/fd/net
CA = r'''
import os, subprocess
out = open("/tmp/d157a.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
def sh(cmd, t=10):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=t)
        return (r.stdout or b"").decode("latin1", "replace") + (r.stderr or b"").decode("latin1", "replace")
    except Exception as e:
        return "EXC %r" % (e,)
p("=== ENVIRON ===")
try:
    env = open("/proc/1/environ", "rb").read()
    for kv in env.split(b"\x00"):
        if kv:
            p("E:", kv.decode("latin1", "replace")[:300])
except Exception as e:
    p("ENV_ERR", repr(e))
p("=== FD_LIST ===")
try:
    fds = os.listdir("/proc/1/fd")
    p("fd_count", len(fds))
    for fd in sorted(fds, key=lambda x: int(x)):
        try:
            tgt = os.readlink(f"/proc/1/fd/{fd}")
            p("fd", fd, "->", tgt)
        except Exception as e:
            p("fd", fd, "ERR", repr(e))
except Exception as e:
    p("FD_ERR", repr(e))
p("=== NET_TCP ===")
p(sh("cat /proc/1/net/tcp 2>&1 | head -20"))
p("=== NET_TCP6 ===")
p(sh("cat /proc/1/net/tcp6 2>&1 | head -20"))
p("=== NET_UDP ===")
p(sh("cat /proc/1/net/udp 2>&1 | head -10"))
p("=== WCHAN ===")
p(sh("cat /proc/1/wchan 2>&1"))
p("=== DONE")
out.close()
'''

# cmdB: gopclntab 从段边界解析 + spawn/auth 包函数提取
CB = r'''
import struct
out = open("/tmp/d157b.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
data = open("/tmp/sinit.bin", "rb").read()
p("size", len(data))
# 段: .gopclntab 应在 0xa33100 (offset 6500608, size 4159689)
cand = 0xa33100
p("header_magic", data[cand:cand+4].hex())
if data[cand:cand+4] == b"\xf1\xff\xff\xff":
    magic = cand
    nfunc = struct.unpack_from("<I", data, magic + 8)[0]
    nfiles = struct.unpack_from("<I", data, magic + 12)[0]
    textStart = struct.unpack_from("<Q", data, magic + 16)[0]
    fnOff = struct.unpack_from("<I", data, magic + 24)[0]
    cuOff = struct.unpack_from("<I", data, magic + 28)[0]
    ftOff = struct.unpack_from("<I", data, magic + 32)[0]
    p("nfunc", nfunc, "nfiles", nfiles, "textStart", hex(textStart))
    p("fnOff", fnOff, "cuOff", cuOff, "ftOff", ftOff)
    ftab = magic + fnOff
    names = []
    k = ftab
    while k < len(data) and len(names) < nfunc + 100:
        e = data.find(b"\x00", k)
        if e < 0:
            break
        nm = data[k:e]
        k = e + 1
        if len(nm) >= 2:
            names.append(nm)
        if k - ftab > 6000000:
            break
    p("name_count", len(names))
    interesting = []
    for nm in names:
        try:
            t = nm.decode("latin1")
        except Exception:
            continue
        tl = t.lower()
        if any(x in tl for x in ["spawn", "sandbox", "cell", "auth", "sign", "verify", "pubkey",
                                 "ed25519", "command", "exec", "socket", "ping", "kill", "pty",
                                 "connect", "vercel", "mount", "proxy", "policy", "network",
                                 "secret", "token", "credential", "cert"]):
            interesting.append(t)
    p("=== FUNCS ===")
    for t in interesting[:800]:
        p("F:", t[:200])
else:
    p("magic mismatch, scanning...")
    # 退路: 全文件找 magic
    for i in range(0, len(data) - 4, 0x100):
        if data[i:i+4] == b"\xf1\xff\xff\xff":
            p("magic_at", hex(i))
            nfunc = struct.unpack_from("<I", data, i + 8)[0]
            p("nfunc_at", nfunc, "textStart", hex(struct.unpack_from("<Q", data, i + 16)[0]))
            break
p("=== DONE")
out.close()
'''

run_cmd(sid, CA, "pid1-intro", timeout=120)
catfile(sid, "/tmp/d157a.txt", "d157a", 9000)

run_cmd(sid, CB, "gopclntab2", timeout=200)
catfile(sid, "/tmp/d157b.txt", "d157b", 15000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
