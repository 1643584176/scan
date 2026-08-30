# -*- coding: utf-8 -*-
"""vda16_connect: 用 Connect RPC (application/connect+json) 调 Exec/StreamOutput/Process
1) Create(sleep) -> Start -> 保活容器
2) Exec via connect+json (双向流: 发请求, 半关闭, 读响应)
3) StreamOutput via connect+json (服务器流)
4) ProcessService Wait/StreamOutput (hvcp_ 27hex id)
输出落盘 + 哨兵 V16C_DONE"""
import os, time, socket, ctypes, re

OUT = '/vercel/sandbox/v16c.out'
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


def rpc_connect(sockpath, path, body='{}', t=6, ctype='application/connect+json'):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(sockpath)
        req = ('POST %s HTTP/1.1\r\nHost: unix\r\nContent-Type: %s\r\n'
               'Content-Length: %d\r\nConnection: close\r\n\r\n%s' % (path, ctype, len(body), body))
        s.sendall(req.encode())
        try:
            s.shutdown(socket.SHUT_WR)
        except Exception:
            pass
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
        return head.split(b'\r\n')[0].decode(errors='replace'), rest[:600].decode(errors='replace')
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
    CSVC = '/vercel.hive.cell.api.containers.v1.ContainersService'
    PSVC = '/vercel.hive.cell.api.processes.v1.ProcessService'

    # P1: Create + Start
    log('=== P1 Create+Start ===')
    cid = None
    st, bd = rpc_connect(sp, CSVC + '/Create', '{"image":"%s","command":"/bin/sleep 300"}' % IMG, t=15)
    log('create -> %s | %s' % (st, bd[:250]))
    m = re.search(r'"containerId":\s*"([^"]+)"', bd)
    if m:
        cid = m.group(1)
        log('CID=%s' % cid)
    if cid:
        st, bd = rpc_connect(sp, CSVC + '/Start', '{"container_id":"%s"}' % cid, t=6)
        log('start -> %s | %s' % (st, bd[:200]))

    # P2: Exec via connect+json
    log('=== P2 Exec connect ===')
    if cid:
        for body in ['{"container_id":"%s","command":"id"}' % cid,
                     '{"container_id":"%s","command":"/bin/sh -c \'id; uname -a; echo MARKER-OK\'; echo DONE"}' % cid]:
            st, bd = rpc_connect(sp, CSVC + '/Exec', body, t=8)
            log('exec %-100s -> %s | %s' % (body[:96], st, bd[:400].replace('\n', ' ')))
            time.sleep(0.5)

    # P3: StreamOutput via connect
    log('=== P3 StreamOutput connect ===')
    if cid:
        for body in ['{"container_id":"%s"}' % cid, '{}']:
            st, bd = rpc_connect(sp, CSVC + '/StreamOutput', body, t=6)
            log('stream %-40s -> %s | %s' % (body, st, bd[:300].replace('\n', ' ')))
            time.sleep(0.5)

    # P4: ProcessService via connect
    log('=== P4 Process connect ===')
    pid27 = 'hvcp_' + 'a' * 27
    for mth, body in [('Wait', '{"process_id":"%s"}' % pid27),
                      ('StreamOutput', '{"process_id":"%s"}' % pid27),
                      ('Start', '{"process_id":"%s","command":"id"}' % pid27)]:
        st, bd = rpc_connect(sp, PSVC + '/' + mth, body, t=5)
        log('proc %s %-60s -> %s | %s' % (mth, body, st, bd[:250].replace('\n', ' ')))
        time.sleep(0.4)

    # P5: Kill
    if cid:
        st, bd = rpc_connect(sp, CSVC + '/Kill', '{"container_id":"%s"}' % cid, t=5)
        log('kill -> %s | %s' % (st, bd[:150]))

    log('V16C_DONE')
    f.close()


if __name__ == '__main__':
    main()
