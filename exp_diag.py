import subprocess, socket, struct, time

def run(cmd, timeout=10):
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=timeout, text=True)
        return (r.stdout + r.stderr)[:400].replace('\n', ' | ')
    except Exception as e:
        return f"ERR {e}"

print("== [0] openssl s_client 基线(上次成功路径) ==")
print(run(["bash", "-c", "echo | timeout 6 openssl s_client -connect 1.1.1.1:443 -servername example.com 2>&1 | head -3"]))

print("== [1] curl https://example.com 直连 ==")
print(run(["bash", "-c", "curl -s -o /dev/null -w '%{http_code} %{remote_ip}' --connect-timeout 6 https://example.com"]))

print("== [2] curl https://1.1.1.1 -resolve 到 example.com ==")
print(run(["bash", "-c", "curl -s -o /dev/null -w '%{http_code}' --connect-timeout 6 --resolve example.com:443:1.1.1.1 https://example.com"]))

# 复现 probe:标准 python socket
def ch():
    # 最小 ClientHello:版本+随机+空sid+3个TLS13套件+压缩+SNI
    sni = b'\x00\x00\x00\x0f\x00\x0d\x00\x00\x0bexample.com'
    ext = sni + b'\x00\x0a\x00\x08\x00\x04\x00\x1d\x00\x17\x00\x18'
    body = b'\x03\x03' + b'\x22'*32 + b'\x00' + b'\x00\x06' + b'\x13\x01\x13\x02\x13\x03' + b'\x01\x00' + struct.pack(">H", len(ext)) + ext
    hs = b'\x01' + struct.pack(">I", len(body)) + body
    return b'\x16\x03\x01' + struct.pack(">H", len(hs)) + hs

s = socket.socket(); s.settimeout(6)
try:
    t0 = time.time()
    s.connect(("1.1.1.1", 443))
    s.sendall(ch())
    data = b''
    while len(data) < 2048:
        try:
            c = s.recv(4096)
        except socket.timeout:
            break
        if not c: break
        data += c
    print(f"== [3] python CH SNI=example.com -> {data[:40].hex() if data else 'EMPTY'} ({time.time()-t0:.2f}s)")
except Exception as e:
    print("[3] ERR", type(e).__name__, e)
finally:
    s.close()

# 无 SNI 对照
s = socket.socket(); s.settimeout(6)
try:
    t0 = time.time()
    s.connect(("1.1.1.1", 443))
    ext2 = b'\x00\x0a\x00\x08\x00\x04\x00\x1d\x00\x17\x00\x18'
    body2 = b'\x03\x03' + b'\x22'*32 + b'\x00' + b'\x00\x06' + b'\x13\x01\x13\x02\x13\x03' + b'\x01\x00' + struct.pack(">H", len(ext2)) + ext2
    hs2 = b'\x01' + struct.pack(">I", len(body2)) + body2
    s.sendall(b'\x16\x03\x01' + struct.pack(">H", len(hs2)) + hs2)
    data = b''
    while len(data) < 2048:
        try:
            c = s.recv(4096)
        except socket.timeout:
            break
        if not c: break
        data += c
    print(f"== [4] python CH 无SNI -> {data[:40].hex() if data else 'EMPTY'} ({time.time()-t0:.2f}s)")
except Exception as e:
    print("[4] ERR", type(e).__name__, e)
finally:
    s.close()
