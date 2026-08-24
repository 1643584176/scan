# 端口保留 + PG 明文强制实验
import subprocess, re, socket, struct, time, sys

def run(cmd, timeout=15):
    try:
        r = subprocess.run(["bash", "-c", cmd], capture_output=True, timeout=timeout)
        return r.stdout.decode(errors='replace') + r.stderr.decode(errors='replace')
    except Exception as e:
        return f"ERR {e}"

def grab_openssl_ch():
    out = run("echo | timeout 8 openssl s_client -connect 1.1.1.1:443 -servername example.com -msg 2>&1 | head -160")
    hb = []
    m1 = re.search(r'>>> TLS 1\.0, RecordHeader[^\n]*\n\s+([0-9a-fA-F ]{14,20})\n', out)
    if m1:
        hb += [p for p in m1.group(1).split() if re.fullmatch(r'[0-9a-fA-F]{2}', p)]
    m2 = re.search(r'>>> TLS [^,]+, Handshake [^\n]*ClientHello\n(.*?)(?=\n<<<|\n>>>|\Z)', out, re.S)
    if not m2:
        raise SystemExit("no CH captured")
    for line in m2.group(1).splitlines():
        for p in line.split():
            if re.fullmatch(r'[0-9a-fA-F]{2}', p):
                hb.append(p)
    return bytes.fromhex(''.join(hb))

def build_sni_ext(names):
    entries = b''
    for n in names:
        nb = n.encode()
        entries += b'\x00' + struct.pack(">H", len(nb)) + nb
    lst = struct.pack(">H", len(entries)) + entries
    return struct.pack(">H", 0) + struct.pack(">H", len(lst)) + lst

def replace_sni(ch, names):
    pos = ch.find(b'\x00\x00\x0bexample.com')
    start = pos - 6
    old_len = 4 + int.from_bytes(ch[start+2:start+4], 'big')
    new = build_sni_ext(names)
    out = ch[:start] + new + ch[start + old_len:]
    j = 9 + 2 + 32 + 1 + ch[9+2+32]
    j += 2 + int.from_bytes(ch[j:j+2], 'big')
    j += 2
    ext_len_field = j
    old_ext_total = int.from_bytes(ch[ext_len_field:ext_len_field+2], 'big')
    new_ext_total = old_ext_total - old_len + len(new)
    out = out[:ext_len_field] + struct.pack(">H", new_ext_total) + out[ext_len_field+2:]
    body_len = len(out) - 9
    out = out[:3] + struct.pack(">H", body_len + 4) + out[5:]
    out = out[:6] + body_len.to_bytes(3, 'big') + out[9:]
    return out

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
    if d[:1] == b'R':
        return "PG-AUTH"
    if d[:1] == b'E':
        return "PG-ERR"
    return "RAW"

def pg_startup(user="postgres", db="postgres"):
    params = f"user\x00{user}\x00database\x00{db}\x00\x00".encode()
    return struct.pack(">II", 8 + len(params), 196608) + params

def probe(host, port, payload, timeout=8, label=""):
    s = socket.socket(); s.settimeout(timeout)
    try:
        t0 = time.time()
        s.connect((host, port))
        s.sendall(payload)
        data = b''
        while len(data) < 4096:
            try:
                c = s.recv(4096)
            except socket.timeout:
                break
            if not c:
                break
            data += c
        return f"{label} {host}:{port} {classify(data)} {data[:40].hex()} ({time.time()-t0:.2f}s)"
    except socket.timeout:
        return f"{label} {host}:{port} TIMEOUT"
    except ConnectionResetError:
        return f"{label} {host}:{port} RST"
    except Exception as e:
        return f"{label} {host}:{port} ERR {type(e).__name__}:{e}"
    finally:
        s.close()

def pg2_probe(host, port, second_payload, timeout=8, label=""):
    """SSLRequest -> 'S' -> 第二段 payload(明文 StartupMessage)"""
    s = socket.socket(); s.settimeout(timeout)
    try:
        t0 = time.time()
        s.connect((host, port))
        s.sendall(struct.pack(">II", 8, 0x04D2162F))
        first = s.recv(64)
        pgtag = classify(first)
        if pgtag == "PG-OK":
            s.sendall(second_payload)
            data = b''
            while len(data) < 4096:
                try:
                    c = s.recv(4096)
                except socket.timeout:
                    break
                if not c:
                    break
                data += c
        else:
            data = b''
        return f"{label} {host}:{port} SSLReq->{pgtag} then {classify(data)} {data[:40].hex()} ({time.time()-t0:.2f}s)"
    except socket.timeout:
        return f"{label} {host}:{port} TIMEOUT"
    except ConnectionResetError:
        return f"{label} {host}:{port} RST"
    except Exception as e:
        return f"{label} {host}:{port} ERR {type(e).__name__}:{e}"
    finally:
        s.close()

ch0 = grab_openssl_ch()
print(f"CH len={len(ch0)}")
ch = replace_sni(ch0, ["example.com"])

# 端口保留实验:SNI=example.com + 不同目标端口
print("[A] 1.1.1.1:8443 SNI=example.com   :", probe("1.1.1.1", 8443, ch, label="A"))
print("[B] 1.1.1.1:8080 SNI=example.com   :", probe("1.1.1.1", 8080, ch, label="B"))
print("[C] 1.1.1.1:22   SNI=example.com   :", probe("1.1.1.1", 22, ch, label="C"))
print("[D] 1.1.1.1:53   SNI=example.com   :", probe("1.1.1.1", 53, ch, label="D"))
print("[E] 1.1.1.1:443  SNI=example.com(对照):", probe("1.1.1.1", 443, ch, label="E"))

# PG 明文强制实验:SSLRequest -> 'S' -> 明文 StartupMessage
print("[F] PG明文 1.1.1.1:5432           :",
      pg2_probe("1.1.1.1", 5432, pg_startup(), label="F"))
print("[G] PG明文 1.1.1.1:443            :",
      pg2_probe("1.1.1.1", 443, pg_startup(), label="G"))
print("[H] PG明文 104.20.23.154:5432     :",
      pg2_probe("104.20.23.154", 5432, pg_startup(), label="H"))
