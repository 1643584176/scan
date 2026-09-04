# -*- coding: utf-8 -*-
"""sandbox 内凭据/OIDC token 提取面 (v49)
P1: env 全量环境变量 (找 OIDC/AWS/VERCEL token)
P2: /proc/1/environ 宿主级 env
P3: 常见 token 位置 (/root/.config, ~/.vercel, /vercel/sandbox 等)
P4: sandbox 内是否可调 vercel.com API (OIDC token 权限面)"""
import base64, json, sys, time, urllib.request, urllib.error
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TOKEN, TEAM, PROJ

NAME = 'env49'

def parse_data(r):
    out = ''
    for line in r.splitlines():
        if '"data"' in line:
            try:
                out += json.loads(line).get('data', '')
            except Exception:
                pass
    return out

api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
time.sleep(3)
body = {"projectId": PROJ, "name": NAME}
for attempt in range(8):
    c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM, body, 90)
    if c == 429:
        print('[create] 429 retry', flush=True)
        time.sleep(20)
        continue
    break
if c != 200:
    print('create fail', c, r[:200], flush=True)
    sys.exit(1)
sid = json.loads(r)['sandbox']['currentSessionId']
print('sid =', sid, flush=True)
time.sleep(8)

GUEST = r'''
echo "== P1: env (敏感过滤) =="
env | grep -iE "token|oidc|aws|vercel|secret|key|credential|auth|bearer|api" | sed 's/=.*/=<redacted-len>/' | head -40
echo "== P1b: env 全量键名 =="
env | cut -d= -f1 | sort | head -60
echo "== P2: /proc/1/environ =="
tr '\0' '\n' < /proc/1/environ 2>/dev/null | grep -iE "token|oidc|aws|vercel|secret|key|cred" | cut -d= -f1 | head -20
echo "== P2b: /proc/1/environ 键名 =="
tr '\0' '\n' < /proc/1/environ 2>/dev/null | cut -d= -f1 | sort | head -40
echo "== P3: token 文件位置 =="
for p in /root/.config /root/.vercel /vercel/sandbox /tmp /home /etc/vercel; do
  ls -la $p 2>/dev/null | head -8
done
find / -maxdepth 4 -name "*token*" -o -maxdepth 4 -name "*.vercel*" 2>/dev/null | head -20
echo "== P4: 环境里 VERCEL_OIDC_TOKEN? =="
if [ -n "$VERCEL_OIDC_TOKEN" ]; then echo "HAS OIDC TOKEN len=${#VERCEL_OIDC_TOKEN}"; else echo "no VERCEL_OIDC_TOKEN"; fi
if [ -n "$VERCEL_TOKEN" ]; then echo "HAS VERCEL_TOKEN len=${#VERCEL_TOKEN}"; else echo "no VERCEL_TOKEN"; fi
echo "== P5: whoami / id / hostname / uname =="
whoami; id; hostname; uname -a
echo DONE
'''
b64 = base64.b64encode(GUEST.encode()).decode()
c, r = cmd(sid, 'sh', ['-c', 'echo %s | base64 -d | sh' % b64], timeout_ms=60000)
print('[guest] %s' % parse_data(r).strip()[:2000], flush=True)

api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
print('CLEANED', flush=True)
