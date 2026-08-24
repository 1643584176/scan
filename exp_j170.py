# 实验J170: 报告1/2成立性验证 - vda写持久化 + 区域对照
# 问题: j169写块100成功但fsync后进程被杀(可能因写在XFS文件系统内区域触发宿主异常)
# 验证: cmdA读块100(j169写是否持久化) -> cmdB写XFS边界外(J36/J37同款)fsync读回 -> cmdC写文件系统内区域对照
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

def catfile(sid, path, label, n=3000):
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
               {"command": "cat", "args": [path], "wait": True, "logs": True, "timeout": 100})
    print(f"=== {label} status {c} ===", flush=True)
    print(r[:n], flush=True)
    return c

NAME = "expj170"
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

# cmdA: 读块100 (j169写入是否持久化) + 读vda大小关键信息
CA = r'''
import os
out = open("/tmp/d170a.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
try:
    fd = os.open("/dev/vda", os.O_RDONLY)
    os.lseek(fd, 512 * 100, 0)
    d = os.read(fd, 64)
    p("block100_first64", d.hex())
    p("is_j169", d[:14] == b"J169WRITETEST")
    # 读 XFS 边界外区域 (从 J36 输出找: 边界外 offset)
    # 先看 superblock 的 blocksize/logstart 等关键字段判断边界
    os.lseek(fd, 0, 0)
    sb = os.read(fd, 512)
    # XFS SB: magic@0, blocksize@4(u32), dblocks@8(u64), rblocks@16...
    import struct
    blocksize = struct.unpack("<I", sb[4:8])[0]
    dblocks = struct.unpack("<Q", sb[8:16])[0]
    p("sb_blocksize", blocksize, "dblocks", dblocks)
    p("total_bytes", blocksize * dblocks)
    os.close(fd)
except Exception as e:
    p("err", repr(e))
p("=== DONE")
out.close()
'''

# cmdB: 写 XFS 数据区之外 (total_bytes 之后) - J36/J37 同款思路
CB = r'''
import os, time, struct
out = open("/tmp/d170b.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
try:
    fd = os.open("/dev/vda", os.O_RDWR)
    p("open_ok")
    os.lseek(fd, 0, 0)
    sb = os.read(fd, 512)
    blocksize = struct.unpack("<I", sb[4:8])[0]
    dblocks = struct.unpack("<Q", sb[8:16])[0]
    total = blocksize * dblocks
    # 目标: total 之后的第一块 (文件系统外, 安全区)
    target = total + 512 * 7
    p("target", target)
    os.lseek(fd, target, 0)
    orig = os.read(fd, 512)
    p("orig_first16", orig[:16].hex())
    test = b"J170OUTTEST" + b"\x11" * (512 - 12)
    os.lseek(fd, target, 0)
    n = os.write(fd, test)
    p("write_n", n)
    os.fsync(fd)
    p("fsync_ok")
    time.sleep(0.5)
    os.lseek(fd, target, 0)
    back = os.read(fd, 512)
    p("readback_match", back == test)
    # 还原
    os.lseek(fd, target, 0)
    os.write(fd, orig)
    os.fsync(fd)
    p("restored")
    os.close(fd)
except Exception as e:
    p("err", repr(e))
p("=== DONE")
out.close()
'''

# cmdC: 写文件系统内区域(块100)对照 - 复现j169
CC = r'''
import os, time
out = open("/tmp/d170c.txt", "w")
def p(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
    out.flush()
try:
    fd = os.open("/dev/vda", os.O_RDWR)
    p("open_ok")
    os.lseek(fd, 512 * 100, 0)
    orig = os.read(fd, 512)
    p("orig_first16", orig[:16].hex())
    test = b"J170INTEST" + b"\x22" * (512 - 11)
    os.lseek(fd, 512 * 100, 0)
    n = os.write(fd, test)
    p("write_n", n)
    try:
        os.fsync(fd)
        p("fsync_ok")
        time.sleep(0.5)
        os.lseek(fd, 512 * 100, 0)
        back = os.read(fd, 512)
        p("readback_match", back == test)
        os.lseek(fd, 512 * 100, 0)
        os.write(fd, orig)
        os.fsync(fd)
        p("restored")
    except Exception as e:
        p("inner_err", repr(e))
    os.close(fd)
except Exception as e:
    p("err", repr(e))
p("=== DONE")
out.close()
'''

steps = [
    ("read-block100", "/tmp/d170a.txt", CA),
    ("write-outside-xfs", "/tmp/d170b.txt", CB),
    ("write-inside-xfs", "/tmp/d170c.txt", CC),
]

for label, marker, code in steps:
    st = run_cmd(sid, code, label, timeout=150)
    time.sleep(2)
    cf = catfile(sid, marker, f"marker[{label}]", 3000)
    if st == "DEAD" or cf == 410:
        print(f"\n!!! DEATH after cmd[{label}] -> trigger = {label}", flush=True)
        break

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
