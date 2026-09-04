# -*- coding: utf-8 -*-
"""非传统面L5: injectionRules 域格式边界 + 动态更新
① 空 allow + inj 精确行为 (n31② curl -s 静默, 未区分 403/连接失败)
② allowedDomains 支持 IP 吗 (169.254.169.254 metadata / 100.64.0.1 网关) + inj 组合
③ allowedDomains 支持通配符吗 (*.vercel.app)
④ 创建后动态 PATCH networkPolicy → 注入规则能否热更新 (动态注入链)
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

ECHO = 'sbx-echo-e29ca9cb.vercel.app'

def mk_sandbox(name, np):
    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (name, TEAM, PROJ))
    time.sleep(2)
    for attempt in range(4):
        c, r = api("POST", "/v4/sandboxes?teamId=%s" % TEAM, {
            "projectId": PROJ, "name": name, "networkPolicy": np}, 60)
        if c == 429:
            log('[create %s] 429, retry %d...' % (name, attempt + 1))
            time.sleep(8)
            continue
        break
    log('[create %s] -> %s | %s' % (name, c, (r or '')[:180].replace(chr(10), ' ')))
    if c != 200:
        return None
    return json.loads(r)['sandbox']['currentSessionId']

def run(sid, tag, cmdline):
    c3, r3 = api("POST", "/v2/sandboxes/sessions/%s/cmd?teamId=%s" % (sid, TEAM),
                 {"command": "sh", "args": ["-c", cmdline],
                  "wait": True, "timeout": 20000, "logs": True}, 35)
    out = parse_data(r3)
    log('[%s] -> %s' % (tag, out[:500].replace(chr(10), ' ')))
    return out

def probe_code(sid, tag, url):
    """精确输出 http_code + 退出码 + body 前 300 字节"""
    run(sid, tag, "curl -s -m 8 -o /tmp/b.txt -w 'CODE=%%{http_code}' %s > /tmp/c.txt 2>&1; echo EXIT=$? >> /tmp/c.txt; [ -f /tmp/b.txt ] && head -c 300 /tmp/b.txt >> /tmp/c.txt; cat /tmp/c.txt" % url)

# ===== ① 空 allow + inj =====
log('===== ① 空 allow + inj 精确行为 =====')
sid = mk_sandbox('l36a', {"mode": "custom", "allowedDomains": [],
                          "injectionRules": [{"domain": ECHO, "headers": {"X-Only": "1"}}]})
if sid:
    time.sleep(3)
    probe_code(sid, 'empty-allow-echo', 'https://%s/' % ECHO)
    api("DELETE", "/v2/sandboxes/l36a?teamId=%s&projectId=%s" % (TEAM, PROJ))
    time.sleep(2)

# ===== ② allowedDomains IP 格式 =====
log('')
log('===== ② allowedDomains IP 格式 =====')
for ip, tag in [('169.254.169.254', 'meta-ip'), ('100.64.0.1', 'gw-ip')]:
    sid = mk_sandbox('l36b', {"mode": "custom", "allowedDomains": [ip]})
    if sid:
        time.sleep(3)
        probe_code(sid, tag, 'http://%s/' % ip)
        api("DELETE", "/v2/sandboxes/l36b?teamId=%s&projectId=%s" % (TEAM, PROJ))
        time.sleep(2)

# ===== ③ 通配符域 =====
log('')
log('===== ③ 通配符域 =====')
sid = mk_sandbox('l36c', {"mode": "custom", "allowedDomains": ["*.vercel.app"]})
if sid:
    time.sleep(3)
    probe_code(sid, 'wildcard', 'https://%s/' % ECHO)
    api("DELETE", "/v2/sandboxes/l36c?teamId=%s&projectId=%s" % (TEAM, PROJ))
    time.sleep(2)

# ===== ④ 动态 PATCH networkPolicy =====
log('')
log('===== ④ 动态 PATCH networkPolicy =====')
sid = mk_sandbox('l36d', {"mode": "custom", "allowedDomains": [ECHO]})
if sid:
    time.sleep(3)
    run(sid, 'before-patch', "curl -s -m 8 https://%s/ | grep -o 'X-Dyn[^,]*' || echo NODYN" % ECHO)
    # PATCH 尝试: 更新 networkPolicy 注入 X-Dyn
    for path, body in [
        ("/v2/sandboxes/l36d?teamId=%s" % TEAM, {"networkPolicy": {"mode": "custom", "allowedDomains": [ECHO], "injectionRules": [{"domain": ECHO, "headers": {"X-Dyn": "1"}}]}}),
        ("/v2/sandboxes/l36d/network-policy?teamId=%s" % TEAM, {"mode": "custom", "allowedDomains": [ECHO], "injectionRules": [{"domain": ECHO, "headers": {"X-Dyn": "1"}}]}),
    ]:
        c, r = api("PATCH", path, body, 30)
        log('[patch %s] -> %s | %s' % (path[:45], c, (r or '')[:200].replace(chr(10), ' ')))
        if c == 200:
            break
        time.sleep(1)
    time.sleep(3)
    run(sid, 'after-patch', "curl -s -m 8 https://%s/ | grep -o 'X-Dyn[^,]*' || echo NODYN" % ECHO)
    api("DELETE", "/v2/sandboxes/l36d?teamId=%s&projectId=%s" % (TEAM, PROJ))

log('DONE')
