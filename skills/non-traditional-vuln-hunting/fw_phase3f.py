# -*- coding: utf-8 -*-
"""Phase3f: 重建沙箱 + 纯白名单直连 api.vercel.com + aud=httpbin token 调 API"""
import sys, time
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
from fw_driver import api, cmd, TEAM, fresh_sandbox_deny_all

TOK = "<REDACTED_OIDC_JWT>"

GUEST = r'''
import subprocess
TOK = 'TOKEN_PLACEHOLDER'
def curl(args):
    r = subprocess.run(['curl', '-s', '-m', '10', '-k'] + args, capture_output=True, text=True)
    print('---', ' '.join(args)[:150], flush=True)
    print('OUT:', r.stdout[:1000], flush=True)
    print('ERR:', r.stderr[:300], flush=True)
curl(['-H', 'Authorization: Bearer ' + TOK, 'https://api.vercel.com/v2/user'])
curl(['https://api.vercel.com/v2/user'])
curl(['-H', 'Authorization: Bearer fake.token.here', 'https://api.vercel.com/v2/user'])
curl(['-H', 'Authorization: Bearer ' + TOK, 'https://api.vercel.com/v2/teams'])
print('done', flush=True)
'''.replace('TOKEN_PLACEHOLDER', TOK)

code = "cat > /tmp/pg8.py <<'PYEOF'\n" + GUEST + "\nPYEOF\npython3 /tmp/pg8.py"

if __name__ == "__main__":
    sid = fresh_sandbox_deny_all("fwtest2")
    time.sleep(2)
    # 纯白名单直连(旧格式 allow 数组)
    body = {"allow": ["api.vercel.com"]}
    c, r = api("POST", "/v2/sandboxes/sessions/%s/network-policy?teamId=%s" % (sid, TEAM), body)
    print('set allow-array:', c, r[:300], flush=True)
    time.sleep(2)
    c, r = cmd(sid, "bash", ["-lc", code], timeout_ms=60000)
    print('cmd:', c, flush=True)
    print(r[:5000], flush=True)
