import subprocess, socket, struct, time

def run(cmd, timeout=15):
    try:
        r = subprocess.run(["bash", "-c", cmd], capture_output=True, timeout=timeout)
        return r.stdout.decode(errors='replace') + r.stderr.decode(errors='replace')
    except Exception as e:
        return f"ERR {e}"

def sni_ext(names):
    entries = b''
    for n in names:
        nb = n.encode()
        entries += b'\x00' + struct.pack(">H", len(nb)) + nb
    lst = struct.pack(">H", len(entries)) + entries
    return struct.pack(">H", 0) + struct.pack(">H", len(lst)) + lst

def clienthello(snis):
    exts = [sni_ext(snis),
        struct.pack(">HH", 10, 8) + b'\x00\x04\x00\x1d\x00\x17\x00\x18',
        struct.pack(">HH", 11, 2) + b'\x01\x00',
        struct.pack(">HH", 13, 8) + b'\x00\x06\x04\x03\x04\x01\x08\x04',
        struct.pack(">HH", 43, 6) + b'\x00\x04\x03\x04\x03\x03',
        struct.pack(">HH", 16, 14) + b'\x0e\x02h2\x08http/1.1',
        struct.pack(">HH", 51, 38) + b'\x00\x24\x00\x1d\x00\x20' + b'\x55'*32]
    ext_data = b''.join(exts)
    body = (b'\x03\x03' + b'\x22'*32 + b'\x00' + struct.pack(">H", 6)
            + b'\x13\x01\x13\x02\x13\x03' + b'\x01\x00'
            + struct.pack(">H", len(ext_data)) + ext_data)
    hs = b'\x01' + struct.pack(">I", len(body))[1:] + body
    return b'\x16\x03\x01' + struct.pack(">H", len(hs)) + hs

# 可靠启动 s_server
run("pkill -f 's_serve[r]'; rm -f /tmp/srv.log")
run("openssl req -x509 -newkey rsa:2048 -keyout /tmp/k.pem -out /tmp/c.pem -days 1 -nodes -subj '/CN=example.com' 2>/dev/null")
run("(openssl s_server -accept 127.0.0.1:4443 -cert /tmp/c.pem -key /tmp/k.pem -msg > /tmp/srv.log 2>&1 &)")
time.sleep(2)

# [1] 我的 CH
print("== [1] my CH -> local s_server ==")
s = socket.socket(); s.settimeout(5)
try:
    s.connect(("127.0.0.1", 4443))
    s.sendall(clienthello(["example.com"]))
    time.sleep(1.2)
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
print("--- srv.log(my CH) ---")
print(run("cat /tmp/srv.log")[-1500:])

# [2] openssl 对照
print("== [2] openssl s_client -> local s_server ==")
print(run("echo | timeout 8 openssl s_client -connect 127.0.0.1:4443 -servername example.com 2>&1 | grep -E 'CIPHER|New|Verify|error' | head -5"))
