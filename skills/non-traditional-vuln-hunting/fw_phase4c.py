# -*- coding: utf-8 -*-
"""Phase4c: 通配符白名单匹配边界测试(*.httpbin.org)"""
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

# 裸域(通配符是否含裸域)
curl(['--resolve', 'httpbin.org:443:34.195.135.204', 'https://httpbin.org/anything'])
# 单级子域(应通)
curl(['--resolve', 'a.httpbin.org:443:34.195.135.204', 'https://a.httpbin.org/'])
# 多级子域
curl(['--resolve', 'x.y.httpbin.org:443:34.195.135.204', 'https://x.y.httpbin.org/'])
# 后缀拼接(边界,关键)
curl(['--resolve', 'httpbin.org.evil.com:443:34.195.135.204', 'https://httpbin.org.evil.com/'])
# 前缀拼接(负控)
curl(['--resolve', 'evilhttpbin.org:443:34.195.135.204', 'https://evilhttpbin.org/'])
print('done', flush=True)
'''

code = "cat > /tmp/pg11.py <<'PYEOF'\n" + GUEST + "\nPYEOF\npython3 /tmp/pg11.py"

if __name__ == "__main__":
    body = {"mode": "custom", "allowedDomains": ["*.httpbin.org"]}
    c, r = api("POST", "/v2/sandboxes/sessions/%s/network-policy?teamId=%s" % (SID, TEAM), body)
    print('set policy:', c, r[:200], flush=True)
    time.sleep(2)
    c, r = cmd(SID, "bash", ["-lc", code], timeout_ms=90000)
    print('cmd:', c, flush=True)
    print(r[:5000], flush=True)
