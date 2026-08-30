# -*- coding: utf-8 -*-
"""quick_celd_probe: 快速验证 cell.sock/23456 的 celld 活性 (新沙箱)
1) /run 下 socket 文件存在性
2) 127.0.0.1:23456 DrivesService/CreateSnapshot 活性 (400 vs 404)
3) /proc/net/unix 影子检查
4) cell.sock(如存在) 同路径探测
输出落盘 + 哨兵 QCELD_DONE"""
import socket, time, os, subprocess

OUT = '/vercel/sandbox/qceld.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


def rpc_tcp(port, path, body='{}', t=5):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(('127.0.0.1', port))
        req = ('POST %s HTTP/1.1\r\nHost: 127.0.0.1:%d\r\nContent-Type: application/json\r\n'
               'Content-Length: %d\r\nConnection: close\r\n\r\n' % (path, port, len(body)))
        s.sendall(req.encode())
        data = b''
        while True:
            try:
                chunk = s.recv(8192)
            except socket.timeout:
                break
            if not chunk:
                break
            data += chunk
        s.close()
        if not data:
            return 'NORESP', ''
        head, _, rest = data.partition(b'\r\n\r\n')
        return head.split(b'\r\n')[0].decode(errors='replace'), rest[:300].decode(errors='replace')
    except Exception as e:
        return 'EXC:%s' % type(e).__name__, ''


def rpc_unix(sockpath, path, body='{}', t=5):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(sockpath)
        req = ('POST %s HTTP/1.1\r\nHost: unix\r\nContent-Type: application/json\r\n'
               'Content-Length: %d\r\nConnection: close\r\n\r\n' % (path, len(body)))
        s.sendall(req.encode())
        data = b''
        while True:
            try:
                chunk = s.recv(8192)
            except socket.timeout:
                break
            if not chunk:
                break
            data += chunk
        s.close()
        if not data:
            return 'NORESP', ''
        head, _, rest = data.partition(b'\r\n\r\n')
        return head.split(b'\r\n')[0].decode(errors='replace'), rest[:300].decode(errors='replace')
    except Exception as e:
        return 'EXC:%s' % type(e).__name__, ''


def sh(cmd, t=6):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=t)
        return (r.stdout + r.stderr).strip()[:400]
    except Exception as e:
        return 'ERR %s' % e


log('=== P1 socket 文件 ===')
for p in ['/run/cell', '/run/vercel/share', '/run/containerd', '/run/apm', '/run/metrics']:
    log('ls %s: %s' % (p, sh('ls -la %s 2>&1' % p)))

log('=== P2 23456 celld 路径活性 ===')
paths = [
    ('/vercel.hive.cell.api.usage.v1.UsageService/GetResourceUsage', '{}'),
    ('/vercel.hive.cell.api.drives.v1.DrivesService/CreateSnapshot', '{}'),
    ('/vercel.hive.cell.api.drives.v1.DrivesService/CreateSnapshot', '{"drive_id":"a"*32}'),
    ('/vercel.hive.cell.api.containers.v1.ContainersService/Create', '{}'),
    ('/vercel.sandbox.spawn.v1.SpawnService/Ping', '{}'),
]
for p, b in paths:
    st, bd = rpc_tcp(23456, p, b)
    log('%s %s -> %s | %s' % (p.split('/')[-1], b[:30], st, bd[:200].replace('\n', ' ')))
    time.sleep(0.5)

log('=== P3 /proc/net/unix 影子 ===')
log(sh('grep -E "cell|containerd|apm|metrics|init" /proc/net/unix 2>/dev/null | head -20'))

log('=== P4 cell.sock 直连 (如存在) ===')
for sp in ['/run/cell/cell.sock', '/run/vercel/share/init.sock']:
    if os.path.exists(sp):
        st, bd = rpc_unix(sp, '/vercel.hive.cell.api.usage.v1.UsageService/GetResourceUsage', '{}')
        log('%s -> %s | %s' % (sp, st, bd[:200].replace('\n', ' ')))
    else:
        log('%s: not exists' % sp)

log('QCELD_DONE')
f.close()
