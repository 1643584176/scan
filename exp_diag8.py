# 双 SNI 解码错误来源 + PG 链转发目标判定
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
        raise SystemExit("no CH captured: " + out[:500])
    for line in m2.group(1).splitlines():
        for p in line.split():
            if re.fullmatch(r'[0-9a-fA-F]{2}', p):
                hb.append(p)
    if not hb:
        raise SystemExit("no hex parsed")
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
    if pos < 0:
        raise SystemExit("SNI marker not found")
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
    return "RAW"

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

def pg_probe(host, port, ch_payload, timeout=8, label=""):
    s = socket.socket(); s.settimeout(timeout)
    try:
        t0 = time.time()
        s.connect((host, port))
        s.sendall(struct.pack(">II", 8, 0x04D2162F))
        first = s.recv(64)
        pgtag = classify(first)
        if pgtag == "PG-OK":
            s.sendall(ch_payload)
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

# 目标:example.com 真实 IP(Cloudflare 104.20.23.154)、1.1.1.1、黑孔 192.0.2.1
print("[A] HTTPS 1.1.1.1 SNI=example.com            :",
      probe("1.1.1.1", 443, replace_sni(ch0, ["example.com"]), label="A"))
print("[B] HTTPS 黑孔 SNI=example.com               :",
      probe("192.0.2.1", 443, replace_sni(ch0, ["example.com"]), label="B"))
print("[C] HTTPS 黑孔 双SNI[example.com,attacker]   :",
      probe("192.0.2.1", 443, replace_sni(ch0, ["example.com", "attacker.invalid"]), label="C"))
print("[D] HTTPS 1.1.1.1 双SNI[ex.com,ex.com]       :",
      probe("1.1.1.1", 443, replace_sni(ch0, ["example.com", "example.com"]), label="D"))
print("[E] HTTPS 104.20.23.154 SNI=example.com      :",
      probe("104.20.23.154", 443, replace_sni(ch0, ["example.com"]), label="E"))
print("[F] HTTPS 104.20.23.154 SNI=attacker.invalid :",
      probe("104.20.23.154", 443, replace_sni(ch0, ["attacker.invalid"]), label="F"))
print("[G] PG链 104.20.23.154:443 SNI=example.com   :",
      pg_probe("104.20.23.154", 443, replace_sni(ch0, ["example.com"]), label="G"))
print("[H] PG链 104.20.23.154:443 SNI=attacker.inv  :",
      pg_probe("104.20.23.154", 443, replace_sni(ch0, ["attacker.invalid"]), label="H"))
print("[I] PG链 104.20.23.154:5432 SNI=example.com  :",
      pg_probe("104.20.23.154", 5432, replace_sni(ch0, ["example.com"]), label="I"))
