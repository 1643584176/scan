# -*- coding: utf-8 -*-
"""N 线矩阵: deniedCIDRs 生效范围完整对照
场景 A: deny 44.223.250.0/24 (httpbin.org 所在网段, allowedDomain 成员)
   A1 curl --resolve 44.223.250.126 -> ?
   A2 connect 44.223.250.126:443 -> ?
   A3 curl --resolve 3.234.68.252 (未 deny 的 httpbin IP) -> ? (应 200)
   A4 connect 3.234.68.252:443 -> ?
   A5 connect 8.8.8.8:53 (未 deny) -> ?
场景 B: 追加 deny 8.8.8.0/24
   B1 connect 8.8.8.8:53 -> ? (上轮 RC 0 = deny 未执行?)
   B2 connect 44.223.250.126:443 -> ? (仍 deny 中)
场景 C: deny-all 对照
   C1 connect 3.234.68.252:443 -> ? (应非 0)
"""
import json, re, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TEAM, PROJ

c, r = api('GET', '/v2/sandboxes/npol1?teamId=%s&projectId=%s' % (TEAM, PROJ))
d = json.loads(r)
sid = d['sandbox']['currentSessionId']
print('npol1 sid:', sid, flush=True)

def parse_data(r):
    out = ''
    for line in r.splitlines():
        if '"data"' in line:
            try:
                out += json.loads(line).get('data', '')
            except Exception:
                pass
    return out

def set_policy(body, tag):
    c, r = api('POST', '/v2/sandboxes/sessions/%s/network-policy?teamId=%s' % (sid, TEAM), body)
    print('[%s] set ->' % tag, c, r[:120], flush=True)
    time.sleep(3)

def conn(ip, port, tag):
    sc = "python3 -c \"import socket; s=socket.socket(); s.settimeout(4); rc=s.connect_ex(('%s',%d)); print('RC_', rc)\"" % (ip, port)
    c, r = cmd(sid, 'sh', ['-c', sc], timeout_ms=30000)
    out = parse_data(r)
    m = re.search(r'RC_ (\d+)', out)
    rc = m.group(1) if m else '?' + out[:60]
    print('[%s] %s:%d -> %s' % (tag, ip, port, rc), flush=True)
    return rc

def curl_ip(ip, tag):
    sc = "curl -sk --max-time 8 --resolve httpbin.org:443:%s https://httpbin.org/anything 2>&1 | head -4" % ip
    c, r = cmd(sid, 'sh', ['-c', sc], timeout_ms=30000)
    out = parse_data(r)
    ok = '"anything"' in out or '"args"' in out
    print('[%s] curl %s -> %s | %s' % (tag, ip, 'OK-200' if ok else 'FAIL', out[:80].replace(chr(10), ' ')), flush=True)
    return ok

# 恢复策略 (上轮结束 deny-all)
set_policy({"mode": "custom", "allowedDomains": ["httpbin.org"]}, 'RECOVER')

# ===== 场景 A: deny 44.223.250.0/24 =====
set_policy({"mode": "custom", "allowedDomains": ["httpbin.org"], "deniedCIDRs": ["44.223.250.0/24"]}, 'A')
curl_ip('44.223.250.126', 'A1')
conn('44.223.250.126', 443, 'A2')
curl_ip('3.234.68.252', 'A3')
conn('3.234.68.252', 443, 'A4')
conn('8.8.8.8', 53, 'A5')

# ===== 场景 B: 追加 deny 8.8.8.0/24 =====
set_policy({"mode": "custom", "allowedDomains": ["httpbin.org"], "deniedCIDRs": ["44.223.250.0/24", "8.8.8.0/24"]}, 'B')
conn('8.8.8.8', 53, 'B1')
conn('44.223.250.126', 443, 'B2')
conn('8.8.4.4', 53, 'B3')

# ===== 场景 C: deny-all =====
set_policy({"mode": "deny-all"}, 'C')
conn('3.234.68.252', 443, 'C1')
conn('44.223.250.126', 443, 'C2')

print('=== N-MATRIX DONE ===', flush=True)
