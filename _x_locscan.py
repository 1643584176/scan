# -*- coding: utf-8 -*-
"""三线: (1) guest 内 localhost 全端口扫描 (找 sandbox-init 管理服务)
(2) 私有网段多 IP:53 DNS 查询覆盖面 (防火墙 DNS 代答边界)
(3) fs/write 端点探测 (控制面文件写面)
"""
import json, sys, time, base64
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

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
c, r = api("POST", "/v2/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": "loc1"})
if c != 200:
    log('create failed: %s' % r[:200]); sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
log('loc1 sid: %s' % sid)
time.sleep(3)

# 1) localhost 端口扫描
log('')
log('===== 1) localhost port scan =====')
SCAN = '''import socket, concurrent.futures
open_ports = []
def chk(p):
    s = socket.socket(); s.settimeout(0.3)
    try:
        if s.connect_ex(('127.0.0.1', p)) == 0: return p
    except Exception: pass
    finally: s.close()
    return None
with concurrent.futures.ThreadPoolExecutor(64) as ex:
    for res in ex.map(chk, range(1, 65536)):
        if res: open_ports.append(res)
print('OPEN', sorted(open_ports))
'''
b64 = base64.b64encode(SCAN.encode()).decode()
c2, out = run_cmd(sid, 'sh', ['-c', 'echo %s | base64 -d | python3' % b64], 120000)
log('scan: %s | %s' % (c2, out[-300:]))

# 监听信息
c2, out = run_cmd(sid, 'sh', ['-c', 'cat /proc/net/tcp /proc/net/tcp6 2>/dev/null | head -40; echo ---; ss -lntp 2>/dev/null | head -20; echo ---; ls -la /proc/*/exe 2>/dev/null | head -20'])
log('listeners: %s' % out[:1200])

# 2) 私有 IP:53 DNS 覆盖面
log('')
log('===== 2) private-range :53 DNS coverage =====')
DNS = '''import socket, struct
def dnsq(ip, port=53):
    s = socket.socket(); s.settimeout(3)
    try:
        rc = s.connect_ex((ip, port))
        if rc != 0: return 'RC%d' % rc
        hdr = struct.pack('!HHHHHH', 0x1234, 0x0100, 1, 0, 0, 0)
        q = b'\\x07example\\x03com\\x00' + struct.pack('!HH', 1, 1)
        s.sendall(hdr + q)
        d = s.recv(512)
        # rcode = 低 4 bit of flags
        flags = struct.unpack('!H', d[2:4])[0]
        return 'RESP %dB rcode=%d' % (len(d), flags & 0xF)
    except Exception as e:
        return 'ERR %s' % type(e).__name__
    finally:
        s.close()
for ip in ['172.31.0.2', '172.31.0.3', '172.31.0.4', '172.31.0.18', '10.0.0.2', '172.31.57.1', '192.168.0.2']:
    print(ip, dnsq(ip), flush=True)
'''
b64 = base64.b64encode(DNS.encode()).decode()
c2, out = run_cmd(sid, 'sh', ['-c', 'echo %s | base64 -d | python3' % b64], 60000)
log('dns: %s' % out[-500:])

# 3) fs/write 端点探测
log('')
log('===== 3) fs/write endpoints =====')
for path, body in [
    ("/v2/sandboxes/sessions/%s/fs/write" % sid, {"path": "/vercel/sandbox/test.txt", "content": base64.b64encode(b'hello').decode()}),
    ("/v2/sandboxes/sessions/%s/fs/upload" % sid, {"path": "/vercel/sandbox/test2.txt", "content": "hello"}),
    ("/v2/sandboxes/sessions/%s/fs/append" % sid, {"path": "/vercel/sandbox/test3.txt", "content": "x"}),
    ("/v2/sandboxes/sessions/%s/files/write" % sid, {"path": "/vercel/sandbox/test4.txt", "content": "y"}),
    ("/v2/sandboxes/sessions/%s/write" % sid, {"path": "/vercel/sandbox/test5.txt"}),
]:
    c3, r3 = api("POST", path + "?teamId=%s" % TEAM, body)
    log('%s -> %s | %s' % (path.split('/')[-1], c3, r3[:200].replace('\n', ' ')))

# 清理
api("DELETE", "/v2/sandboxes/loc1?teamId=%s&projectId=%s" % (TEAM, PROJ))
log('DONE')
