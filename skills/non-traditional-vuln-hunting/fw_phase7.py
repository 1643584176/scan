# -*- coding: utf-8 -*-
"""Phase7: subnets 格式测试 - deny=0.0.0.0/0 是否全拦 + allow 语义"""
import sys, time
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
from fw_driver import api, cmd, TEAM

SID = "sbx_BQJ2aL59BOiIDLDpm6guM4rpiJih"

GUEST = r'''
import subprocess
def curl(args):
    r = subprocess.run(['curl', '-s', '-m', '6', '-k'] + args, capture_output=True, text=True)
    print('---', ' '.join(args)[:120], flush=True)
    print('RC=%d OUT:%s ERR:%s' % (r.returncode, r.stdout[:200].replace(chr(10),' '), r.stderr[:150].replace(chr(10),' ')), flush=True)

curl(['https://httpbin.org/anything'])
curl(['https://www.example.com/'])
print('done', flush=True)
'''

code = "cat > /tmp/pg15.py <<'PYEOF'\n" + GUEST + "\nPYEOF\npython3 /tmp/pg15.py"

if __name__ == "__main__":
    # subnets.deny=0.0.0.0/0 (期望全拦; 若 httpbin 仍通 => deny 未生效 = bypass)
    body = {"subnets": {"deny": ["0.0.0.0/0"]}}
    c, r = api("POST", "/v2/sandboxes/sessions/%s/network-policy?teamId=%s" % (SID, TEAM), body)
    print('set subnets.deny-all:', c, r[:300], flush=True)
    time.sleep(2)
    c, r = cmd(SID, "bash", ["-lc", code], timeout_ms=60000)
    print('cmd:', c, flush=True)
    print(r[:4000], flush=True)
