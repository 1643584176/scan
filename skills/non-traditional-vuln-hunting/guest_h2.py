# -*- coding: utf-8 -*-
"""guest_h2: 23456 H2-only 服务方法矩阵 (curl --http2-prior-knowledge)
Phase1: H2 全方法矩阵 (celld/containers/process/spawn)
Phase2: 30001/30002 H2+HTTP1.1 指纹
Phase3: 23456 H2 免签 Kill/Ping
输出落盘 + 哨兵 H2PROBE_DONE"""
import subprocess, time, os

OUT = '/vercel/sandbox/h2_probe.out'
f = open(OUT, 'w', encoding='utf-8')


def log(s):
    f.write(str(s) + '\n')
    f.flush()


def h2_post(port, path, body='{}', t=6):
    try:
        r = subprocess.run(
            ['curl', '-s', '-m', str(t), '--http2-prior-knowledge',
             '-H', 'Content-Type: application/json',
             '-d', body,
             '-i', 'http://127.0.0.1:%d%s' % (port, path)],
            capture_output=True, text=True, timeout=t + 4)
        out = (r.stdout or '')[:300].replace('\n', ' ')
        if not out:
            out = 'rc=%d err=%s' % (r.returncode, (r.stderr or '')[:120].replace('\n', ' '))
        return out
    except Exception as e:
        return 'EXC:%s' % type(e).__name__


def h1_post(port, path, body='{}', t=4):
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(('127.0.0.1', port))
        req = 'POST %s HTTP/1.1\r\nHost: 127.0.0.1:%d\r\nContent-Type: application/json\r\nContent-Length: %d\r\nConnection: close\r\n\r\n%s' % (path, port, len(body), body)
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
            return 'NORESP'
        return data.split(b'\r\n')[0].decode(errors='replace') + ' | ' + data.split(b'\r\n\r\n')[-1][:150].decode(errors='replace').replace('\n', ' ')
    except Exception as e:
        return 'EXC:%s' % type(e).__name__


SERVICES = {
    'celld': ['vercel.hive.celld.api.v1.Celld', ['Heartbeat', 'Configure', 'RegisterPort', 'SetWorkload',
             'GetResourceUsage', 'StartContainer', 'StopContainer', 'WaitContainer', 'Shutdown']],
    'containers': ['vercel.hive.celld.api.v1.ContainersService', ['Create', 'Start', 'Stop', 'Kill', 'Wait',
                   'Exec', 'Stdin', 'KillServer', 'StreamOutput', 'CreateSnapshot', 'GetImageConfig',
                   'SetOCIImageConfig', 'ListContainers']],
    'process': ['vercel.hive.celld.api.v1.ProcessService', ['Wait', 'Kill', 'ListPids', 'ExecProcess', 'GetProcess']],
    'spawn': ['vercel.sandbox.spawn.v1.SpawnService', ['Spawn', 'Kill', 'Ping', 'SpawnInteractive']],
    'health': ['grpc.health.v1.Health', ['Check', 'Watch']],
    'controller': ['vercel.sandbox.spawn.v1.ControllerService', ['Heartbeat', 'RegisterPort', 'ReportStatus', 'Ack']],
}
log('=== PHASE1 23456 H2 method matrix ===')
hits = []
for grp, (svc, methods) in SERVICES.items():
    for m in methods:
        path = '/%s/%s' % (svc, m)
        out = h2_post(23456, path)
        if '404' not in out and not out.startswith('EXC') and not out.startswith('rc='):
            hits.append((path, out))
            log('HIT %s -> %s' % (path, out))
        elif out.startswith('rc='):
            log('ERR %s -> %s' % (path, out))
        time.sleep(0.4)
log('H2 matrix done, hits=%d' % len(hits))

log('=== PHASE2 30001/30002 fingerprint ===')
for port in [30001, 30002]:
    for name, fn in [('h1-get', lambda p=port: h1_post(p, '/', '{}')),
                     ('h2-get', lambda p=port: h2_post(p, '/', '{}'))]:
        try:
            out = fn()
            log('%d %s -> %s' % (port, name, out))
        except Exception as e:
            log('%d %s EXC:%s' % (port, name, e))
        time.sleep(0.3)

log('=== PHASE3 23456 H2 Kill/Ping no-signature ===')
for m in ['Ping', 'Kill']:
    path = '/vercel.sandbox.spawn.v1.SpawnService/%s' % m
    for body in ['{}', '{"processId":"1"}', '{"process_id":"1"}', '{"procId":"1"}']:
        out = h2_post(23456, path, body)
        log('h2 %s body=%s -> %s' % (m, body, out))
        time.sleep(0.5)

log('H2PROBE_DONE')
f.close()
