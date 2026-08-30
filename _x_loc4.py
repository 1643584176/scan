# -*- coding: utf-8 -*-
"""跟进四线: (1) strings 分析 sandbox-init 找路由/域名 (2) init.sock 直连探测 (3) VPC 内网 IP 枚举+AXFR (4) fs/write multipart 修复"""
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

c, r = api("POST", "/v2/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": "loc4"})
if c != 200:
    log('create failed: %s' % r[:200]); sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
log('loc4 sid: %s' % sid)
time.sleep(3)

# 1) strings 分析 sandbox-init
log('')
log('===== 1) sandbox-init strings =====')
c2, out = run_cmd(sid, 'sh', ['-c', 'which strings >/dev/null 2>&1 && strings /run/vercel/share/sandbox-init | grep -E "https?://|vercel\\.(com|internal)|\\\\.internal" | sort -u | head -60 || echo NO_STRINGS'], 60000)
log('urls: %s' % out[:2000])
c2, out = run_cmd(sid, 'sh', ['-c', 'strings /run/vercel/share/sandbox-init | grep -E "^/[a-zA-Z0-9_.-]{2,40}$" | sort -u | head -120'], 60000)
log('paths: %s' % out[:3000])

# 2) init.sock 直连探测
log('')
log('===== 2) init.sock probe =====')
SOCK = '''import socket
def probe(payload, timeout=2):
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect('/run/vercel/share/init.sock')
        s.sendall(payload)
        try:
            d = s.recv(1024)
            return repr(d[:300])
        except Exception as e:
            return 'NORESP:%s' % type(e).__name__
    except Exception as e:
        return 'ERR:%s' % type(e).__name__
    finally:
        s.close()
print('get /', probe(b'GET / HTTP/1.0\\r\\nHost: localhost\\r\\n\\r\\n'), flush=True)
print('opt *', probe(b'OPTIONS * HTTP/1.1\\r\\nHost: localhost\\r\\n\\r\\n'), flush=True)
print('empty', probe(b''), flush=True)
paths = ['/healthz','/api','/v1','/metrics','/cmd','/fs','/exec','/run','/version','/status','/ws','/proxy','/token','/env','/sandbox','/session']
for p in paths:
    print(p, probe(b'GET ' + p.encode() + b' HTTP/1.0\\r\\nHost: localhost\\r\\n\\r\\n'), flush=True)
'''
b64 = base64.b64encode(SOCK.encode()).decode()
c2, out = run_cmd(sid, 'sh', ['-c', 'echo %s | base64 -d | python3' % b64], 90000)
log(out[-2500:])

# 3) VPC 内网枚举 + AXFR + hosted zone 猜测
log('')
log('===== 3) VPC enum =====')
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
    s.settimeout(2.5)
    try:
        s.sendto(build_query(name, qtype), (ip, 53))
        d, _ = s.recvfrom(512)
        flags = struct.unpack('!H', d[2:4])[0]
        rcode = flags & 0xF
        ancount = struct.unpack('!H', d[6:8])[0]
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
                nm = b''
                j = 0
                while j < len(rdata):
                    ll = rdata[j]
                    if ll == 0: break
                    if ll & 0xC0 == 0xC0: nm += b'.'; j += 2; break
                    nm += rdata[j+1:j+1+ll] + b'.'
                    j += 1 + ll
                out.append('PTR:' + nm.decode(errors='replace'))
            else:
                out.append('t%d:%dB' % (typ, rdlen))
        return 'rcode=%d an=%d %s' % (rcode, ancount, out)
    except Exception as e:
        return 'ERR:%s' % type(e).__name__
    finally:
        s.close()
# 内网 IP 枚举 (172.31.0.0/24 前 30 + 10.0.0.0/24 前 10 + 172.31.57.1)
hits = []
for i in list(range(1, 31)) + [57]:
    r = query('172.31.0.2', 'ip-172-31-0-%d.ec2.internal' % i)
    tag = 'HIT' if 'an=1' in r else ''
    if tag: hits.append('172.31.0.%d' % i)
    print('172.31.0.%d' % i, r, flush=True)
for i in range(1, 11):
    r = query('172.31.0.2', 'ip-10-0-0-%d.ec2.internal' % i)
    if 'an=1' in r: hits.append('10.0.0.%d' % i)
    print('10.0.0.%d' % i, r, flush=True)
r = query('172.31.0.2', 'ip-172-31-57-1.ec2.internal')
if 'an=1' in r: hits.append('172.31.57.1')
print('172.31.57.1', r, flush=True)
print('HITS', hits, flush=True)
# AXFR
print('AXFR ec2.internal', query('172.31.0.2', 'ec2.internal', 252), flush=True)
# hosted zone 猜测
for z in ['db.internal','pg.internal','redis.internal','api.internal','postgres.vercel.internal','vercel.db','sandbox.vercel.internal','svc.internal','pg.vercel.internal','internal.vercel.com']:
    r = query('172.31.0.2', z)
    print('%-28s' % z, r, flush=True)
'''
b64 = base64.b64encode(DNS.encode()).decode()
c2, out = run_cmd(sid, 'sh', ['-c', 'echo %s | base64 -d | python3' % b64], 120000)
log(out[-4000:])

# 4) fs/write multipart 修复
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
mp = (b'--' + bnd.encode() + b'\r\nContent-Disposition: form-data; name="file"; filename="t.txt"\r\n'
      b'Content-Type: text/plain\r\n\r\nhello\r\n--' + bnd.encode() + b'--\r\n')
c3, r3 = api_ct('POST', '/v2/sandboxes/sessions/%s/fs/write?teamId=%s' % (sid, TEAM), raw=mp, ct='multipart/form-data; boundary=' + bnd)
log('multipart -> %s | %s' % (c3, r3[:250].replace('\n', ' ')))
c3, r3 = api("GET", "/v2/sandboxes/sessions/%s/fs/read?teamId=%s&path=/vercel" % (sid, TEAM))
log('fs/read -> %s | %s' % (c3, r3[:200].replace('\n', ' ')))

api("DELETE", "/v2/sandboxes/loc4?teamId=%s&projectId=%s" % (TEAM, PROJ))
log('DONE')
