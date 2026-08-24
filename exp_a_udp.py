import socket, struct, time

# --- UDP DNS 查询到 8.8.8.8:53 ---
def dns_query(domain, server=("8.8.8.8", 53), timeout=5):
    qname = b"".join(bytes([len(p)]) + p.encode() for p in domain.split(".")) + b"\x00"
    pkt = struct.pack(">HHHHHH", 0x1234, 0x0100, 1, 0, 0, 0) + qname + struct.pack(">HH", 1, 1)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(timeout)
    t0 = time.time()
    try:
        s.sendto(pkt, server)
        data, addr = s.recvfrom(4096)
        return f"UDP-RESPONSE from {addr} in {time.time()-t0:.2f}s len={len(data)}"
    except socket.timeout:
        return "UDP-TIMEOUT (blocked?)"
    except Exception as e:
        return f"UDP-ERROR: {e}"
    finally:
        s.close()

# --- TCP 对照:连接 8.8.8.8:80 ---
def tcp_test(server=("8.8.8.8", 80), timeout=5):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    t0 = time.time()
    try:
        s.connect(server)
        return f"TCP-CONNECTED to {server} in {time.time()-t0:.2f}s"
    except socket.timeout:
        return "TCP-TIMEOUT (blocked as expected)"
    except Exception as e:
        return f"TCP-BLOCKED: {e}"
    finally:
        s.close()

print("[1]", dns_query("example.com"))
print("[2]", tcp_test())
