# -*- coding: utf-8 -*-
"""Phase4: 白名单匹配逻辑测试 - 子域/后缀/边界域名 + 直连是否注入 OIDC token"""
import sys, time
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
from fw_driver import api, cmd, TEAM

SID = "sbx_BQJ2aL59BOiIDLDpm6guM4rpiJih"

GUEST = r'''
import subprocess
def curl(args):
    r = subprocess.run(['curl', '-s', '-m', '8', '-k'] + args, capture_output=True, text=True)
    print('---', ' '.join(args)[:130], flush=True)
    print('RC=%d OUT:%s ERR:%s' % (r.returncode, r.stdout[:400].replace(chr(10),' '), r.stderr[:200].replace(chr(10),' ')), flush=True)

# A. 直连 httpbin(验证是否注入 OIDC token)
curl(['https://httpbin.org/anything'])
# B. 子域(不存在)
curl(['https://a.httpbin.org/'])
# C. 后缀拼接(不存在)
curl(['https://httpbin.org.evil.com/'])
# D. 不同域(负控)
curl(['https://example.com/'])
print('done', flush=True)
'''

code = "cat > /tmp/pg9.py <<'PYEOF'\n" + GUEST + "\nPYEOF\npython3 /tmp/pg9.py"

if __name__ == "__main__":
    # 配置 custom: 仅 httpbin.org 白名单, 无 forwardURL 规则
    body = {"mode": "custom", "allowedDomains": ["httpbin.org"]}
    c, r = api("POST", "/v2/sandboxes/sessions/%s/network-policy?teamId=%s" % (SID, TEAM), body)
    print('set policy:', c, r[:300], flush=True)
    time.sleep(2)
    c, r = cmd(SID, "bash", ["-lc", code], timeout_ms=90000)
    print('cmd:', c, flush=True)
    print(r[:6000], flush=True)
