# -*- coding: utf-8 -*-
"""sandbox 细节面 (v50)
P1: sudo 免密检查 (ubuntu 在 sudo 组)
P2: opencode 配置内容 (可能含 token)
P3: CA bundle 路径详情 (代理架构线索)
P4: /proc/net 网络架构 (loopback 代理? 宿主网络?)
P5: k8s/docker 线索 (service account, socket)
P6: 隐藏进程/服务 (ps aux, ss -tlnp)"""
import base64, json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TEAM, PROJ

NAME = 'env50'

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
for attempt in range(8):
    c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM, {"projectId": PROJ, "name": NAME}, 90)
    if c == 429:
        print('[create] 429 retry', flush=True)
        time.sleep(20)
        continue
    break
if c != 200:
    print('create fail', c, (r or '')[:200], flush=True)
    sys.exit(1)
sid = json.loads(r)['sandbox']['currentSessionId']
print('sid =', sid, flush=True)
time.sleep(8)

GUEST = r'''
echo "== P1: sudo =="
echo | sudo -S -l 2>&1 | head -15
echo "== P1b: sudo -n true =="
sudo -n true 2>&1 && echo "SUDO_NOPASSWD_OK" || echo "SUDO_NEEDS_PASS"
echo "== P2: opencode 配置 =="
find /root/.config/opencode /tmp/opencode /home/ubuntu -name "*.json" -o -name "auth*" -o -name "*token*" 2>/dev/null | head
cat /root/.config/opencode/* 2>/dev/null | head -20
ls -la /tmp/opencode 2>/dev/null
echo "== P3: CA bundle =="
echo "SSL_CERT_FILE=$SSL_CERT_FILE"
echo "CURL_CA_BUNDLE=$CURL_CA_BUNDLE"
echo "AWS_CA_BUNDLE=$AWS_CA_BUNDLE"
ls -la $SSL_CERT_FILE 2>/dev/null
head -5 $SSL_CERT_FILE 2>/dev/null
echo "== P3b: 环境变量全量 =="
env | sort
echo "== P4: 网络架构 =="
ip addr 2>/dev/null | head -30
ip route 2>/dev/null
cat /etc/resolv.conf
echo "== P5: k8s/docker =="
ls -la /var/run/docker.sock 2>&1
ls -la /run/containerd 2>&1 | head -5
find / -maxdepth 5 -name "*.json" -path "*serviceaccount*" 2>/dev/null | head
echo "== P6: 进程/端口 =="
ps aux --sort=-pid 2>/dev/null | head -20
ss -tlnp 2>/dev/null | head -20
cat /proc/net/tcp 2>/dev/null | head -10
echo DONE
'''
b64 = base64.b64encode(GUEST.encode()).decode()
c, r = cmd(sid, 'sh', ['-c', 'echo %s | base64 -d | sh' % b64], timeout_ms=60000)
print('[guest] %s' % parse_data(r).strip()[:2500], flush=True)

api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (NAME, TEAM, PROJ))
print('CLEANED', flush=True)
