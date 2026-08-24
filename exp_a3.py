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

ntp = b'\x23' + b'\x00' * 47
stun = struct.pack(">HHI", 0x0001, 0x0000, 0x2112A442) + b'\x00' * 16

print("[UDP-NTP]", udp_probe("216.239.35.0", 123, ntp))
print("[UDP-STUN]", udp_probe("74.125.200.127", 19302, stun))
print("[UDP-8.8.8.8:53]", udp_probe("8.8.8.8", 53, stun))

# TCP 对照组:未允许的 IP
def tcp_test(server, port, timeout=6):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    t0 = time.time()
    try:
        s.connect((server, port))
        s.send(b"GET / HTTP/1.0\r\nHost: test\r\n\r\n")
        data = s.recv(200)
        return f"TCP {server}:{port} CONNECTED resp={data[:60]!r} {time.time()-t0:.2f}s"
    except socket.timeout:
        return f"TCP {server}:{port} TIMEOUT (blocked?)"
    except Exception as e:
        return f"TCP {server}:{port} BLOCKED {e}"
    finally:
        s.close()

print("[TCP-1.1.1.1:80]", tcp_test("1.1.1.1", 80))
print("[TCP-example.com:80]", tcp_test("93.184.216.34", 80))  # example.com IP 直连
