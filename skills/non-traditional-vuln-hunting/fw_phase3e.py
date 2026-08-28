# -*- coding: utf-8 -*-
"""Phase3e: aud=httpbin token 调 Vercel API 的行为验证 + api.vercel.com 纯白名单直连"""
import sys, time
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
from fw_driver import api, cmd, TEAM

SID = "sbx_6M8Yg7kJadsCnQ8GlDyTeZJa6VaY"
TOK = "<REDACTED_OIDC_JWT>"

GUEST = r'''
import subprocess

TOK = 'TOKEN_PLACEHOLDER'
def curl(args):
    r = subprocess.run(['curl', '-s', '-m', '10', '-k'] + args, capture_output=True, text=True)
    print('---', ' '.join(args)[:120], flush=True)
    print('OUT:', r.stdout[:800], flush=True)
    print('ERR:', r.stderr[:300], flush=True)

# 1. 用 aud=httpbin token 调 API(当前策略: api.vercel.com 会被转发到 httpbin)
curl(['-H', 'Authorization: Bearer ' + TOK, 'https://api.vercel.com/v2/user'])
# 2. 无 token 基线
curl(['https://api.vercel.com/v2/user'])
# 3. 假 token
curl(['-H', 'Authorization: Bearer fake.token.here', 'https://api.vercel.com/v2/user'])
print('done', flush=True)
'''.replace('TOKEN_PLACEHOLDER', TOK)

code = "cat > /tmp/pg7.py <<'PYEOF'\n" + GUEST + "\nPYEOF\npython3 /tmp/pg7.py"

if __name__ == "__main__":
    # 当前策略仍是 allow: api.vercel.com -> forwardURL httpbin (上一轮配置成功)
    c, r = cmd(SID, "bash", ["-lc", code], timeout_ms=60000)
    print('cmd:', c, flush=True)
    print(r[:5000], flush=True)
