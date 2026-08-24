import socket, struct, time

def udp_probe(server, port, payload, timeout=6, label=""):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(timeout)
    t0 = time.time()
    try:
        s.sendto(payload, (server, port))
        data, addr = s.recvfrom(4096)
        return f"{label}{server}:{port} RESP len={len(data)} {time.time()-t0:.2f}s"
    except socket.timeout:
        return f"{label}{server}:{port} TIMEOUT"
    except Exception as e:
        return f"{label}{server}:{port} ERR {e}"
    finally:
        s.close()

# NTP 请求包 (版本3 客户端模式)
ntp = b'\x23' + b'\x00' * 47
# STUN binding request (简单 STUN 头)
stun = struct.pack(">HHI", 0x0001, 0x0000, 0x2112A442) + b'\x00' * 16

print("[NTP]", udp_probe("216.239.35.0", 123, ntp, label=""))
print("[STUN]", udp_probe("74.125.200.127", 19302, stun, label=""))
print("[UDP123-8.8.8.8]", udp_probe("8.8.8.8", 123, ntp, label=""))

# ICMP ping (需要 root)
try:
    import os
    r = os.system("ping -c 2 -W 2 8.8.8.8 2>&1 | tail -3")
except Exception as e:
    print("[ICMP] ERR", e)

# IPv6 检查
try:
    s6 = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    s6.settimeout(4)
    t0 = time.time()
    s6.sendto(ntp, ("2001:4860:4860::8888", 123))
    data, addr = s6.recvfrom(4096)
    print(f"[IPv6-UDP] RESP len={len(data)} {time.time()-t0:.2f}s")
    s6.close()
except socket.timeout:
    print("[IPv6-UDP] TIMEOUT")
except Exception as e:
    print(f"[IPv6-UDP] ERR {e}")
