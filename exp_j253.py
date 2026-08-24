# 实验J253: 解析目录块内容 - 提取 /dev/vda 文件名 (判定磁盘归属)
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

NAME = "expj253"
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
import subprocess
code = (
    "import os\n"
    "fd = os.open('/dev/vda', os.O_RDONLY)\n"
    "blocks = [0x40000, 0x42000, 0xa9000, 0xab000]\n"
    "def dump(blk):\n"
    "    os.lseek(fd, blk, 0)\n"
    "    b = os.read(fd, 4096)\n"
    "    print('BLK', hex(blk), 'magic', b[:4], flush=True)\n"
    "    # 简单 ASCII 片段提取\n"
    "    cur = ''\n"
    "    out = []\n"
    "    for c in b:\n"
    "        if 32 <= c < 127:\n"
    "            cur += chr(c)\n"
    "        else:\n"
    "            if len(cur) >= 2:\n"
    "                out.append(cur)\n"
    "            cur = ''\n"
    "    if len(cur) >= 2:\n"
    "        out.append(cur)\n"
    "    print('  frags:', out[:30], flush=True)\n"
    "    # 尝试结构化解析 (dir3 data: header 0x40, entries namelen@i)\n"
    "    i = 0x40\n"
    "    names = []\n"
    "    while i < 4096 - 16:\n"
    "        nl = b[i]\n"
    "        if nl == 0 or nl > 255:\n"
    "            break\n"
    "        ino = int.from_bytes(b[i+4:i+12], 'big')\n"
    "        nm = b[i+12:i+12+nl]\n"
    "        if all(32 <= c < 127 for c in nm):\n"
    "            names.append((ino, nm.decode(errors='replace')))\n"
    "            i += 12 + nl\n"
    "            i = (i + 7) & ~7\n"
    "        else:\n"
    "            break\n"
    "    print('  parsed:', names[:20], flush=True)\n"
    "for blk in blocks:\n"
    "    try:\n"
    "        dump(blk)\n"
    "    except Exception as e:\n"
    "        print('BLK', hex(blk), 'ERR', e, flush=True)\n"
    "os.close(fd)\n"
)
try:
    r = subprocess.run(["sudo", "-n", "python3", "-c", code], capture_output=True, text=True, timeout=20)
    print("A rc", r.returncode, (r.stdout + r.stderr)[:3000].replace(chr(10), "|"), flush=True)
except Exception as e:
    print("A EXC", type(e).__name__, str(e)[:100], flush=True)
print("DONE_A", flush=True)
'''
run_cmd(sid, CODE_A, "A_PARSE", timeout=100)

CODE_B = r'''
import subprocess
code = (
    "import os\n"
    "fd = os.open('/dev/vda', os.O_RDONLY)\n"
    "# root inode 1024: 找 AG0 inode 区 - ino 1024 的 chunk 位于 inode 区偏移 (1024/64)*32KB\n"
    "# inode 区起点未知, 在 16KB-4MB 间搜 'IN' magic + version 3 + ino 匹配\n"
    "import struct\n"
    "BS = 512\n"
    "found = []\n"
    "for base in range(0x4000, 0x400000, BS):\n"
    "    os.lseek(fd, base, 0)\n"
    "    b = os.read(fd, BS)\n"
    "    if b[:2] == b'IN':\n"
    "        mode = struct.unpack('>H', b[2:4])[0]\n"
    "        ver = b[4]\n"
    "        fmt = b[5]\n"
    "        ino = struct.unpack('>Q', b[0x90:0x98])[0]\n"
    "        if ino == 1024:\n"
    "            print('ROOT_INODE at', hex(base), 'mode', oct(mode), 'ver', ver, 'fmt', fmt, flush=True)\n"
    "            # v3 inode: size@0x40, nextents@0x54, forkoff@0x5a, aformat@0x5b\n"
    "            size = struct.unpack('>Q', b[0x40:0x48])[0]\n"
    "            nextents = struct.unpack('>I', b[0x54:0x58])[0]\n"
    "            forkoff = b[0x5a]\n"
    "            aformat = b[0x5b]\n"
    "            print('  size', size, 'nextents', nextents, 'forkoff', forkoff, 'aformat', aformat, flush=True)\n"
    "            # data fork extents 在 offset 0xa8 之后 (v3: crc 区后) - 若 forkoff==0 则 data 区从 0xa8 开始\n"
    "            dfork = 0xa8\n"
    "            for e in range(min(nextents, 8)):\n"
    "                off = dfork + e * 16\n"
    "                rec = b[off:off+16]\n"
    "                print('  ext', e, rec.hex(), flush=True)\n"
    "            found.append(base)\n"
    "            break\n"
    "print('DONE_FIND', len(found), flush=True)\n"
    "os.close(fd)\n"
)
try:
    r = subprocess.run(["sudo", "-n", "python3", "-c", code], capture_output=True, text=True, timeout=25)
    print("B rc", r.returncode, (r.stdout + r.stderr)[:2500].replace(chr(10), "|"), flush=True)
except Exception as e:
    print("B EXC", type(e).__name__, str(e)[:100], flush=True)
print("DONE_B", flush=True)
'''
run_cmd(sid, CODE_B, "B_ROOTINO", timeout=100)

CODE_C = r'''
import subprocess
code = (
    "import os\n"
    "fd = os.open('/dev/vda', os.O_RDONLY)\n"
    "BS = 4096\n"
    "START = 64 * 1024 * 1024\n"
    "RANGE = 64 * 1024 * 1024\n"
    "hits = []\n"
    "off = START\n"
    "bufsz = 4 * 1024 * 1024\n"
    "while off < START + RANGE:\n"
    "    os.lseek(fd, off, 0)\n"
    "    d = os.read(fd, bufsz)\n"
    "    if not d:\n"
    "        break\n"
    "    nb = len(d) // BS\n"
    "    for i in range(nb):\n"
    "        if d[i*BS:i*BS+4] == b'XDD3':\n"
    "            hits.append(off + i * BS)\n"
    "    off += len(d)\n"
    "print('HITS_64_128M', len(hits), flush=True)\n"
    "for h in hits[:20]:\n"
    "    print('DIR', hex(h), flush=True)\n"
    "os.close(fd)\n"
)
try:
    r = subprocess.run(["sudo", "-n", "python3", "-c", code], capture_output=True, text=True, timeout=60)
    print("C rc", r.returncode, (r.stdout + r.stderr)[:1200].replace(chr(10), "|"), flush=True)
except Exception as e:
    print("C EXC", type(e).__name__, str(e)[:100], flush=True)
print("DONE_C", flush=True)
'''
run_cmd(sid, CODE_C, "C_SCAN2", timeout=120)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
