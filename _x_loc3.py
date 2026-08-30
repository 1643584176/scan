# -*- coding: utf-8 -*-
"""跟进四线: (1) UNIX socket 权限检查 (2) AWS VPC 内网 DNS 解析 (3) 23456 Go mux 路径枚举 (4) fs/write multipart"""
import json, sys, time, base64
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ, BASE, TOKEN

def log(s):
    print(s, flush=True)

def run_cmd(sid, command, args, timeout_ms=30000):
    c, r = api("POST", "/v2/sandboxes/sessions/%s/cmd?teamId=%s" % (sid, TEAM),
               {"command": command, "args": args, "wait": True, "logs": True, "timeout": timeout_ms})
    out = ''
    for line in r.splitlines():
        if '"data"' in line:
            try: out += json.loads(line).get('data', '')
            except Exception: pass
    return c, out

# 建沙箱
c, r = api("POST", "/v2/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": "loc3"})
if c != 200:
    log('create failed: %s' % r[:200]); sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
log('loc3 sid: %s' % sid)
time.sleep(3)

# 1) UNIX socket 权限
log('')
log('===== 1) unix socket perms =====')
c2, out = run_cmd(sid, 'sh', ['-c', 'for s in /run/vercel/share/init.sock /run/metrics/metrics.sock /run/apm/apm.sock /run/cell/cell.sock /run/containerd/containerd.sock /run/containerd/containerd.sock.ttrpc /run/apm/apm.sock; do ls -la $s 2>/dev/null; stat -c "  mode=%a owner=%U:%G" $s 2>/dev/null; done; echo ===; id; ls -la /run/vercel/share/ 2>/dev/null'], 30000)
log(out[:2000])

# 2) AWS VPC 内网 DNS
log('')
log('===== 2) VPC internal DNS =====')
DNS = '''import socket, struct
def build_query(name, qtype=1):
    hdr = struct.pack('!HHHHHH', 0x1234, 0x0100, 1, 0, 0, 0)
    q = b''
    for part in name.rstrip('.').split('.'):
        q += bytes([len(part)]) + part.encode()
    q += b'\\x00' + struct.pack('!HH', qtype, 1)
    return hdr + q
def query(ip, name, qtype=1):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(3)
    try:
        s.sendto(build_query(name, qtype), (ip, 53))
        d, _ = s.recvfrom(512)
        flags = struct.unpack('!H', d[2:4])[0]
        rcode = flags & 0xF
        ancount = struct.unpack('!H', d[6:8])[0]
        # parse answers
        out = []
        off = 12
        while True:
            l = d[off]
            if l == 0: off += 1; break
            if l & 0xC0 == 0xC0: off += 2; break
            off += l + 1
        off += 4
        for i in range(ancount):
            l = d[off]
            if l & 0xC0 == 0xC0: off += 2
            else:
                while d[off] != 0: off += 1 + d[off]
                off += 1
            typ, cls, ttl, rdlen = struct.unpack('!HHIH', d[off:off+10])
            off += 10
            rdata = d[off:off+rdlen]; off += rdlen
            if typ == 1 and rdlen == 4:
                out.append(socket.inet_ntoa(rdata))
            elif typ == 12:
                out.append('PTR:' + repr(rdata[:60]))
            elif typ == 5:
                out.append('CNAME:' + repr(rdata[:60]))
            else:
                out.append('t%d:%dB' % (typ, rdlen))
        return 'rcode=%d an=%d %s' % (rcode, ancount, out)
    except Exception as e:
        return 'ERR:%s' % type(e).__name__
    finally:
        s.close()
tests = [
    ('A', 'example.com'),
    ('A', 'ec2.internal'),
    ('A', 'compute.internal'),
    ('A', 'ip-172-31-0-2.ec2.internal'),
    ('A', 'ip-172-31-0-3.ec2.internal'),
    ('A', 'ip-10-0-0-2.ec2.internal'),
    ('PTR', '2.0.31.172.in-addr.arpa'),
    ('PTR', '3.0.31.172.in-addr.arpa'),
    ('A', 'vercel.internal'),
    ('A', 'sandbox.internal'),
]
for typ, name in tests:
    print('%-40s' % name, query('172.31.0.2', name, 12 if typ == 'PTR' else 1), flush=True)
'''
b64 = base64.b64encode(DNS.encode()).decode()
c2, out = run_cmd(sid, 'sh', ['-c', 'echo %s | base64 -d | python3' % b64], 60000)
log(out[-2000:])

# 3) 23456 Go mux 路径枚举
log('')
log('===== 3) 23456 path enum =====')
ENUM = '''import socket
paths = ['/healthz','/health','/api','/api/v1','/v1','/metrics','/debug/pprof/','/debug/vars','/version','/status','/ping','/ready','/info','/env','/cmd','/fs','/sandbox','/session','/proxy','/ws','/websocket','/events','/logs','/exec','/rpc','/run','/share','/init','/token','/config']
for p in paths:
    s = socket.socket(); s.settimeout(2)
    try:
        s.connect(('127.0.0.1', 23456))
        s.sendall(('GET %s HTTP/1.0\\r\\nHost: localhost\\r\\n\\r\\n' % p).encode())
        import time; time.sleep(0.25)
        d = s.recv(512)
        line = d.split(b'\\r\\n')[0] if d else b'EMPTY'
        print(p, line.decode(errors='replace'), len(d), flush=True)
    except Exception as e:
        print(p, 'ERR', type(e).__name__, flush=True)
    finally:
        s.close()
'''
b64 = base64.b64encode(ENUM.encode()).decode()
c2, out = run_cmd(sid, 'sh', ['-c', 'echo %s | base64 -d | python3' % b64], 90000)
log(out[-2500:])

# 4) fs/write multipart
log('')
log('===== 4) fs/write multipart =====')
import urllib.request, urllib.error
def api_ct(method, path, raw=None, ct=None):
    req = urllib.request.Request(BASE + path, method=method)
    req.add_header('Authorization', 'Bearer ' + TOKEN)
    if ct:
        req.add_header('Content-Type', ct)
    try:
        with urllib.request.urlopen(req, data=raw, timeout=30) as r:
            return r.status, r.read().decode()[:300]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]

bnd = '----XyZ123'
mp = (b'--' + bnd + b'\\r\\nContent-Disposition: form-data; name="file"; filename="t.txt"\\r\\n'
      b'Content-Type: text/plain\\r\\n\\r\\nhello\\r\\n--' + bnd + b'--\\r\\n')
c3, r3 = api_ct('POST', '/v2/sandboxes/sessions/%s/fs/write?teamId=%s' % (sid, TEAM), raw=mp, ct='multipart/form-data; boundary=' + bnd)
log('multipart -> %s | %s' % (c3, r3[:250].replace('\\n', ' ')))
# 顺带试试 GET /v2/sandboxes/sessions/{sid}/fs?path= 是否可读
c3, r3 = api("GET", "/v2/sandboxes/sessions/%s/fs/read?teamId=%s&path=/vercel" % (sid, TEAM))
log('fs/read -> %s | %s' % (c3, r3[:200].replace('\\n', ' ')))

# 清理
api("DELETE", "/v2/sandboxes/loc3?teamId=%s&projectId=%s" % (TEAM, PROJ))
log('DONE')
