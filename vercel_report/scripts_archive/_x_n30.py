# -*- coding: utf-8 -*-
"""非传统面L: v3 injectionRules/env 字段差异深挖
v4 拒绝 s3Key; v3 接受 injectionRules/env — 验证:
① v4 对 injectionRules/env 是否也接受 (版本差异判定)
② readback: injectionRules 是否保存/回显
③ 行为: guest 访问 allow 域名, 是否真的注入自定义头 (httpbin.org/headers 验证)
④ env: 创建时注入 FOO=bar, guest 内 echo 是否生效; VERCEL_OIDC_TOKEN 是否被过滤
⑤ 若注入生效: 头注入到 Vercel 资产 (vercel.app) 组合 Host 伪造的潜力
"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, TEAM, PROJ

def log(s): print(s, flush=True)

def parse_data(r):
    out = ''
    for line in (r or '').splitlines():
        if '"data"' in line:
            try:
                out += json.loads(line).get('data', '')
            except Exception:
                pass
    return out

def fresh(name, body_extra=None, version='v4'):
    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (name, TEAM, PROJ))
    time.sleep(2)
    body = {"projectId": PROJ, "name": name}
    if body_extra:
        body.update(body_extra)
    c, r = api("POST", "/%s/sandboxes?teamId=%s" % (version, TEAM), body, 60)
    log('[create %s %s] -> %s | %s' % (version, name, c, (r or '')[:200].replace(chr(10), ' ')))
    if c != 200:
        return None, r
    return json.loads(r)['sandbox'], r

# ===== ① v4 vs v3: injectionRules / env 接受度 =====
log('===== ① v4 对照 =====')
for tag, extra in [
    ('v4-inj', {"networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"],
               "injectionRules": [{"domain": "httpbin.org", "headers": {"X-T": "1"}}]}}),
    ('v4-env', {"env": {"FOO": "bar"}}),
    ('v4-ports', {"ports": [8080]}),
]:
    c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM,
               {"projectId": PROJ, "name": "l30", **extra}, 60)
    log('[%s] -> %s | %s' % (tag, c, (r or '')[:250].replace(chr(10), ' ')))
    if c == 200:
        api("DELETE", "/v2/sandboxes/l30?teamId=%s&projectId=%s" % (TEAM, PROJ))
        time.sleep(1)

# ===== ② v3 injectionRules: readback + 行为 =====
log('')
log('===== ② v3 injectionRules =====')
sb, r = fresh('l30a', {"networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"],
                       "injectionRules": [{"domain": "httpbin.org", "headers": {"X-T": "1", "X-Test-2": "abc"}}]}},
              version='v3')
if sb:
    sid = sb['currentSessionId']
    time.sleep(3)
    # readback
    c2, r2 = api("GET", "/v2/sandboxes/l30a?teamId=%s&projectId=%s" % (TEAM, PROJ), None, 20)
    try:
        np = json.loads(r2)['sandbox'].get('networkPolicy')
        log('readback np: %s' % json.dumps(np)[:400])
    except Exception as e:
        log('readback err %s | %s' % (e, (r2 or '')[:200]))
    # 行为: httpbin.org/headers 看注入头
    c3, r3 = api("POST", "/v2/sandboxes/sessions/%s/cmd?teamId=%s" % (sid, TEAM),
                 {"command": "sh", "args": ["-c",
                  "curl -s -m 8 https://httpbin.org/headers 2>&1 | head -30"],
                  "wait": True, "timeout": 15000, "logs": True}, 30)
    out = parse_data(r3)
    log('headers resp: %s' % out[:600].replace(chr(10), ' '))
    api("DELETE", "/v2/sandboxes/l30a?teamId=%s&projectId=%s" % (TEAM, PROJ))

# ===== ③ v3 env: 注入 + 保留变量过滤 =====
log('')
log('===== ③ v3 env =====')
sb, r = fresh('l30b', {"env": {"FOO": "bar", "VERCEL_OIDC_TOKEN": "should_be_filtered",
                               "VERCEL_TOKEN": "should_be_filtered2"}}, version='v3')
if sb:
    sid = sb['currentSessionId']
    time.sleep(3)
    c3, r3 = api("POST", "/v2/sandboxes/sessions/%s/cmd?teamId=%s" % (sid, TEAM),
                 {"command": "sh", "args": ["-c", "echo FOO=$FOO; echo OIDC=${VERCEL_OIDC_TOKEN:0:12}; "
                  "echo VTOK=${VERCEL_TOKEN:0:12}; echo ALL=$(env | wc -l)"],
                  "wait": True, "timeout": 15000, "logs": True}, 30)
    log('env resp: %s' % parse_data(r3).replace(chr(10), ' '))
    api("DELETE", "/v2/sandboxes/l30b?teamId=%s&projectId=%s" % (TEAM, PROJ))

log('DONE')
