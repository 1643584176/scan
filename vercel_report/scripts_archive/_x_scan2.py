# -*- coding: utf-8 -*-
"""D 线放行面延伸: 宿主网络服务扫描 (数据层判定)
Q1: 扫描 172.31.0.2 (DNS 代答 IP) 候选端口 -> 真实服务?
Q2: 扫描 100.64.0.1/0.2/0.3 (CGNAT 网关) 候选端口
Q3: 数据层探测 (HTTP/TLS/PG/DNS 协议判定, 非 connect 判定)
"""
import base64, json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TEAM, PROJ

c, r = api('GET', '/v2/sandboxes/npol1?teamId=%s&projectId=%s' % (TEAM, PROJ))
d = json.loads(r)
sid = d['sandbox']['currentSessionId']
print('npol1 sid:', sid, 'status:', d['sandbox']['status'], flush=True)
if d['sandbox'].get('status') != 'running':
    c, r = api('GET', '/v2/sandboxes/npol1?teamId=%s&projectId=%s&resume=true' % (TEAM, PROJ))
    d = json.loads(r)
    sid = d['sandbox']['currentSessionId']
    print('resumed sid:', sid, flush=True)
    time.sleep(5)

def run(tag, sc, maxlen=1400):
    c, r = cmd(sid, 'sh', ['-c', sc], timeout_ms=120000)
    out = ''
    for line in r.splitlines():
        if '"data"' in line:
            try:
                out += json.loads(line).get('data', '')
            except Exception:
                pass
    print('[%s] %s' % (tag, out[:maxlen]), flush=True)
    return out

SCAN_CODE = '''import socket, struct, time
TARGETS = [('172.31.0.2', [22, 53, 80, 443, 2379, 3000, 5000, 5432, 6379, 8000, 8080, 8443, 9090, 26661, 10250]),
           ('100.64.0.1', [22, 53, 80, 443, 2379, 3000, 5432, 6379, 8000, 8080, 26661]),
           ('100.64.0.2', [22, 53, 80, 443, 2379, 3000, 5432, 6379, 8000, 8080, 26661]),
           ('100.64.0.3', [22, 53, 80, 443, 2379, 3000, 5432, 6379, 8000, 8080, 26661])]
def probe(ip, port):
    try:
        s = socket.socket()
        s.settimeout(3)
        rc = s.connect_ex((ip, port))
        if rc != 0:
            s.close(); return 'CLOSED(%d)' % rc
        # 数据层探测
        payload = None
        if port == 80 or port == 8000 or port == 8080 or port == 3000:
            payload = b'GET / HTTP/1.0\\r\\nHost: x\\r\\n\\r\\n'
        elif port == 443 or port == 8443:
            payload = bytes.fromhex('16030100400100003c0303') + b'0' * 54  # TLS hello 前导
        elif port == 5432:
            payload = struct.pack('!II', 8, 80877103)
        elif port == 53:
            payload = struct.pack('!HHHHHH', 0x1234, 0x0100, 1, 0, 0, 0) + b'\\x07example\\x03com\\x00' + struct.pack('!HH', 1, 1)
        else:
            payload = b'hello\\r\\n'
        try:
            s.sendall(payload)
            s.settimeout(4)
            d = s.recv(64)
            if len(d) > 0:
                return 'DATA:' + repr(d[:40])
            return 'CONNECTED-NODATA'
        except socket.timeout:
            return 'CONNECTED-TIMEOUT'
        except Exception as e:
            return 'CONNECTED-ERR:%s' % type(e).__name__
    except Exception as e:
        return 'ERR:%s' % type(e).__name__
for ip, ports in TARGETS:
    for p in ports:
        r = probe(ip, p)
        if not r.startswith('CLOSED'):
            print('OPEN %s:%d -> %s' % (ip, p, r), flush=True)
        else:
            print('x %s:%d %s' % (ip, p, r))
print('SCAN_DONE')
'''

b64 = base64.b64encode(SCAN_CODE.encode()).decode()
run('Q1-scan', 'echo %s | base64 -d | python3' % b64, maxlen=1800)

print('=== SCAN DONE ===', flush=True)
