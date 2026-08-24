# 验证抓取的 openssl CH 是否有效:重放给本地 s_server
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
    # RecordHeader 段(5 字节:16 03 01 xx xx)
    m1 = re.search(r'>>> TLS 1\.0, RecordHeader[^\n]*\n\s+([0-9a-fA-F ]{14,20})\n', out)
    if m1:
        hb += [p for p in m1.group(1).split() if re.fullmatch(r'[0-9a-fA-F]{2}', p)]
    # ClientHello 段
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

def parse_ch(ch):
    """解析 CH 字段,返回 dict"""
    assert ch[0] == 0x16
    rec_len = int.from_bytes(ch[3:5], 'big')
    assert len(ch) == 5 + rec_len, f"record len mismatch: {len(ch)} vs {5+rec_len}"
    hs_len = int.from_bytes(ch[6:9], 'big')
    body = ch[9:9+hs_len]
    j = 0
    ver = body[j:j+2]; j += 2
    rnd = body[j:j+32]; j += 32
    sid_len = body[j]; j += 1
    sid = body[j:j+sid_len]; j += sid_len
    cip_len = int.from_bytes(body[j:j+2], 'big'); j += 2
    cips = body[j:j+cip_len]; j += cip_len
    assert body[j] == 1; j += 1
    comp = body[j]; j += 1
    ext_len = int.from_bytes(body[j:j+2], 'big'); j += 2
    exts = {}
    end = j + ext_len
    assert end == len(body), f"ext end {end} != body len {len(body)}"
    while j < end:
        t = int.from_bytes(body[j:j+2], 'big')
        l = int.from_bytes(body[j+2:j+4], 'big')
        exts[t] = body[j+4:j+4+l]
        j += 4 + l
    assert j == end
    return {"rec_len": rec_len, "hs_len": hs_len, "version": ver.hex(),
            "sid_len": sid_len, "ciphers": len(cips)//2, "exts": exts}

ch0 = grab_openssl_ch()
p = parse_ch(ch0)
print(f"CH len={len(ch0)} rec_len={p['rec_len']} hs_len={p['hs_len']} ver={p['version']} sid_len={p['sid_len']} ciphers={p['ciphers']}")
print("exts:", sorted(p['exts'].keys()))

# 起 s_server
run("pkill -f 's_serve[r]'; rm -f /tmp/srv.log")
run("openssl req -x509 -newkey rsa:2048 -keyout /tmp/k.pem -out /tmp/c.pem -days 1 -nodes -subj '/CN=example.com' 2>/dev/null")
run("(openssl s_server -accept 127.0.0.1:4443 -cert /tmp/c.pem -key /tmp/k.pem -msg -naccept 10 > /tmp/srv.log 2>&1 &)")
time.sleep(2)

# 基线:openssl s_client 连本地(对照)
print("== [1] openssl s_client -> local s_server ==")
print(run("echo | timeout 6 openssl s_client -connect 127.0.0.1:4443 -servername example.com 2>&1 | grep -E 'CIPHER is|New,' | head -2"))

# 重放抓到的 CH
print("== [2] replay openssl CH -> local s_server ==")
s = socket.socket(); s.settimeout(5)
try:
    s.connect(("127.0.0.1", 4443))
    s.sendall(ch0)
    time.sleep(1.0)
    resp = b''
    try:
        while True:
            c = s.recv(4096)
            if not c: break
            resp += c
    except socket.timeout: pass
    print("   resp:", resp[:80].hex() if resp else "EMPTY")
except Exception as e:
    print("   ERR", type(e).__name__, e)
finally:
    s.close()

print("--- srv.log ---")
print(run("cat /tmp/srv.log")[-1200:])
