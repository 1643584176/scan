# -*- coding: utf-8 -*-
"""Phase4d: 通配符判别 - 用真实子域 www.example.com 验证通配符是否生效"""
import sys, time
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
from fw_driver import api, cmd, TEAM

SID = "sbx_BQJ2aL59BOiIDLDpm6guM4rpiJih"

GUEST = r'''
import subprocess
def curl(args):
    r = subprocess.run(['curl', '-s', '-m', '8', '-k'] + args, capture_output=True, text=True)
    print('---', ' '.join(args)[:150], flush=True)
    print('RC=%d OUT:%s ERR:%s' % (r.returncode, r.stdout[:250].replace(chr(10),' '), r.stderr[:250].replace(chr(10),' ')), flush=True)

# 真实子域(通配符应放行; DNS 也应放行)
curl(['https://www.example.com/'])
# 裸域(--resolve 绕过 DNS)
curl(['--resolve', 'example.com:443:172.66.147.243', 'https://example.com/'])
# 边界: 后缀拼接
curl(['--resolve', 'example.com.evil.com:443:172.66.147.243', 'https://example.com.evil.com/'])
print('done', flush=True)
'''

code = "cat > /tmp/pg12.py <<'PYEOF'\n" + GUEST + "\nPYEOF\npython3 /tmp/pg12.py"

if __name__ == "__main__":
    body = {"mode": "custom", "allowedDomains": ["*.example.com"]}
    c, r = api("POST", "/v2/sandboxes/sessions/%s/network-policy?teamId=%s" % (SID, TEAM), body)
    print('set policy:', c, r[:200], flush=True)
    time.sleep(2)
    c, r = cmd(SID, "bash", ["-lc", code], timeout_ms=90000)
    print('cmd:', c, flush=True)
    print(r[:4500], flush=True)
