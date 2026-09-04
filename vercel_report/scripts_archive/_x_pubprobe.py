# -*- coding: utf-8 -*-
"""P 线实验 4: custom 模式下公网 IP 数据层可达性验证 (区分 connect 模拟 vs 真实转发)"""
import json, re, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TEAM, PROJ

c, r = api('GET', '/v2/sandboxes/dmode3?teamId=%s&projectId=%s' % (TEAM, PROJ))
d = json.loads(r)
sid = d['sandbox']['currentSessionId']
print('dmode3 sid:', sid, flush=True)

GUEST = '''
import socket, time
OUT = '/vercel/sandbox/pubprobe.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    f.write(line + '\\n'); f.flush(); print(line, flush=True)

def probe(ip, port, payload, tag, wait=3):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(4)
        s.connect((ip, port))
        if payload:
            s.sendall(payload)
        s.settimeout(wait)
        d = b''
        try:
            while True:
                ch = s.recv(4096)
                if not ch: break
                d += ch
                if len(d) > 300: break
        except socket.timeout:
            pass
        s.close()
        log('P %s %s:%d -> DATA %r' % (tag, ip, port, d[:200]))
    except (ConnectionResetError, BrokenPipeError):
        log('P %s %s:%d -> RST' % (tag, ip, port))
    except socket.timeout:
        log('P %s %s:%d -> TIMEOUT' % (tag, ip, port))
    except OSError as e:
        log('P %s %s:%d -> OSERR:%s' % (tag, ip, port, e.errno))
    except Exception as e:
        log('P %s %s:%d -> EXC:%s' % (tag, ip, port, type(e).__name__))

log('START')
HTTP = b'GET / HTTP/1.1\\r\\nHost: one.one.one.one\\r\\nConnection: close\\r\\n\\r\\n'
# P1 公网 443 明文 HTTP (对照: allow-all 下应返回 cloudflare 400)
probe('1.1.1.1', 443, HTTP, 'pub443-plain')
# P2 公网 80 明文 HTTP
probe('1.1.1.1', 80, HTTP, 'pub80-plain')
# P3 公网 22 (SSH banner)
probe('1.1.1.1', 22, b'', 'pub22-nodata')
# P4 公网 53 TCP DNS
probe('8.8.8.8', 53, b'\\x12\\x34\\x01\\x00\\x00\\x01\\x00\\x00\\x00\\x00\\x00\\x00\\x07example\\x03com\\x00\\x00\\x01\\x00\\x01', 'pub53-dns')
# P5 对照: 私有网段 172.31 5432 (已知模拟 b'S')
probe('172.31.0.2', 5432, b'\\x00\\x00\\x00\\x08\\x04\\xd2\\x16\\x2f', 'vpc5432-pg')
# P6 对照: 公网 443 TLS ClientHello 到任意 IP (httpbin.org 已 allow)
probe('1.1.1.1', 443, b'\\x16\\x03\\x01\\x02\\x00\\x01\\x00\\x01\\xfc\\x03\\x03\\x00' + b'\\x00' * 32 + b'\\x00\\x00\\x02\\x00\\x2f', 'pub443-tls')
log('PUBPROBE_DONE')
f.close()
'''
import base64
b64 = base64.b64encode(GUEST.encode()).decode()
inj = "import base64;open('/vercel/sandbox/pubprobe.py','wb').write(base64.b64decode('%s'))" % b64
c, r = cmd(sid, 'python3', ['-c', inj], timeout_ms=30000)
print('inject:', c, flush=True)
time.sleep(1)
c, r = cmd(sid, 'python3', ['/vercel/sandbox/pubprobe.py'], timeout_ms=120000)
print('run:', c, flush=True)
for attempt in range(12):
    time.sleep(4)
    c, r = cmd(sid, 'cat', ['/vercel/sandbox/pubprobe.out'], timeout_ms=30000)
    if c == 200 and 'PUBPROBE_DONE' in r:
        print('=== PUB PROBE RESULT ===', flush=True)
        for line in r.splitlines():
            if '"data"' in line:
                try:
                    print(json.loads(line).get('data', ''), flush=True)
                except Exception:
                    pass
        break
    print('wait %d status=%d' % (attempt, c), flush=True)

print('=== PUB DONE ===', flush=True)
