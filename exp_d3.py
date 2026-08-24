import socket, struct, time

# ---------- TLS 1.3 ClientHello 构造(修正所有扩展长度字段) ----------

def sni_ext(names):
    """SNI 扩展,支持多个 name(标准格式)"""
    entries = b''
    for n in names:
        nb = n.encode()
        entries += b'\x00' + struct.pack(">H", len(nb)) + nb
    lst = struct.pack(">H", len(entries)) + entries
    return struct.pack(">H", 0) + struct.pack(">H", len(lst)) + lst

def clienthello(snis, with_sni=True):
    """完整标准 TLS 1.3 ClientHello(openssl 兼容格式)"""
    exts = []
    if with_sni:
        exts.append(sni_ext(snis))
    exts += [
        struct.pack(">HH", 10, 8) + b'\x00\x04\x00\x1d\x00\x17\x00\x18',   # supported_groups
        struct.pack(">HH", 11, 2) + b'\x01\x00',                          # ec_point_formats
        struct.pack(">HH", 13, 8) + b'\x00\x06\x04\x03\x04\x01\x08\x04',  # signature_algorithms
        struct.pack(">HH", 43, 6) + b'\x00\x04\x03\x04\x03\x03',          # supported_versions (1.3+1.2)
        struct.pack(">HH", 16, 14) + b'\x0e\x02h2\x08http/1.1',           # ALPN
        struct.pack(">HH", 51, 38) + b'\x00\x24\x00\x1d\x00\x20' + b'\x55'*32,  # key_share x25519
    ]
    ext_data = b''.join(exts)
    body = (b'\x03\x03' + b'\x22'*32 + b'\x00' + struct.pack(">H", 6)
            + b'\x13\x01\x13\x02\x13\x03' + b'\x01\x00'
            + struct.pack(">H", len(ext_data)) + ext_data)
    hs = b'\x01' + struct.pack(">I", len(body))[1:] + body  # 3字节长度
    return b'\x16\x03\x01' + struct.pack(">H", len(hs)) + hs

def pg_sslrequest():
    return struct.pack(">II", 8, 0x04D2162F)

# ---------- 探测 ----------

def classify(d):
    if not d:
        return "CLOSE(no-data)"
    if d[0] == 0x16:
        return "ServerHello/TLS"
    if d[0] == 0x15:
        return "Alert"
    if d[:1] == b'S':
        return "PG-OK"
    if d[:1] == b'N':
        return "PG-NO"
    return "RAW"

def probe(host, port, payload, timeout=6, label="", pre_recv=False):
    """连接 -> (可选先读) -> 发送 payload -> 收集响应分类"""
    s = socket.socket()
    s.settimeout(timeout)
    try:
        t0 = time.time()
        s.connect((host, port))
        if pre_recv:
            first = s.recv(64)
            pgtag = classify(first)
        else:
            first = b''
            pgtag = ''
        s.sendall(payload)
        data = b''
        while len(data) < 2048:
            try:
                chunk = s.recv(4096)
            except socket.timeout:
                break
            if not chunk:
                break
            data += chunk
        dt = time.time() - t0
        if pgtag:
            return f"{label} {host}:{port} pre={pgtag} then {classify(data)} {data[:40].hex()} ({dt:.2f}s)"
        return f"{label} {host}:{port} {classify(data)} {data[:40].hex()} ({dt:.2f}s)"
    except socket.timeout:
        return f"{label} {host}:{port} TIMEOUT"
    except ConnectionResetError:
        return f"{label} {host}:{port} RST"
    except Exception as e:
        return f"{label} {host}:{port} ERR {type(e).__name__}:{e}"
    finally:
        s.close()

def pg_probe(host, port, ch_payload, timeout=6, label=""):
    """PG 链:connect -> SSLRequest -> recv('S') -> TLS CH -> recv"""
    s = socket.socket()
    s.settimeout(timeout)
    try:
        t0 = time.time()
        s.connect((host, port))
        s.sendall(pg_sslrequest())
        first = s.recv(64)
        pgtag = classify(first)
        if pgtag == "PG-OK":
            s.sendall(ch_payload)
            data = b''
            while len(data) < 2048:
                try:
                    chunk = s.recv(4096)
                except socket.timeout:
                    break
                if not chunk:
                    break
                data += chunk
        else:
            data = b''
        dt = time.time() - t0
        return f"{label} {host}:{port} SSLReq->{pgtag} then {classify(data)} {data[:40].hex()} ({dt:.2f}s)"
    except socket.timeout:
        return f"{label} {host}:{port} TIMEOUT"
    except ConnectionResetError:
        return f"{label} {host}:{port} RST"
    except Exception as e:
        return f"{label} {host}:{port} ERR {type(e).__name__}:{e}"
    finally:
        s.close()

# ---------- 测试矩阵 ----------
if __name__ == "__main__":
    print("[A] HTTPS 基线 SNI=example.com        :",
          probe("1.1.1.1", 443, clienthello(["example.com"]), label="A"))
    print("[B] 双SNI [example.com,attacker.inv]  :",
          probe("1.1.1.1", 443, clienthello(["example.com", "attacker.invalid"]), label="B"))
    print("[C] 双SNI [attacker.inv,example.com]  :",
          probe("1.1.1.1", 443, clienthello(["attacker.invalid", "example.com"]), label="C"))
    print("[D] 未授权 SNI=attacker.invalid       :",
          probe("1.1.1.1", 443, clienthello(["attacker.invalid"]), label="D"))
    print("[E] PG链 443 SNI=example.com          :",
          pg_probe("1.1.1.1", 443, clienthello(["example.com"]), label="E"))
    print("[F] PG链 443 SNI=attacker.invalid     :",
          pg_probe("1.1.1.1", 443, clienthello(["attacker.invalid"]), label="F"))
    print("[G] PG链 12345 SNI=example.com        :",
          pg_probe("1.1.1.1", 12345, clienthello(["example.com"]), label="G"))
    print("[H] PG链 443 无SNI                    :",
          pg_probe("1.1.1.1", 443, clienthello([], with_sni=False), label="H"))
