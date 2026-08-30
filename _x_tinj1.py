# -*- coding: utf-8 -*-
"""T 线: transform/injectionRules API 格式摸索 + 注入行为验证
目标: 确认注入 header 的转发路由依据 (SNI vs HTTP Host)"""
import json, sys, time
sys.path.insert(0, r'F:\scan\skills\non-traditional-vuln-hunting')
sys.stdout.reconfigure(encoding='utf-8')
from vercel_driver import api, cmd, TEAM, PROJ

# 创建沙箱 (allow-all 便于测试注入)
name = 'tinj1'
api('DELETE', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (name, TEAM, PROJ))
time.sleep(2)
c, r = api('POST', '/v2/sandboxes?teamId=%s' % TEAM, {"projectId": PROJ, "name": name})
print('create:', c, r[:150], flush=True)
sid = json.loads(r)['sandbox']['currentSessionId']
print('sid:', sid, flush=True)
time.sleep(3)

# 尝试格式 1: allow 结构 (SDK 格式)
body1 = {
    "mode": "custom",
    "allow": {
        "httpbin.org": [
            {"transform": [{"headers": {"Authorization": "Bearer INJMARK_9f31a2c7"}}]}
        ],
        "*": []
    }
}
c, r = api('POST', '/v2/sandboxes/sessions/%s/network-policy?teamId=%s' % (sid, TEAM), body1)
print('fmt1 allow+transform ->', c, r[:300], flush=True)
time.sleep(2)

# 检查 readback
c2, r2 = api('GET', '/v2/sandboxes/%s?teamId=%s&projectId=%s' % (name, TEAM, PROJ))
try:
    d2 = json.loads(r2)
    print('readback session_pol:', json.dumps(d2.get('session', {}).get('networkPolicy'))[:400], flush=True)
except Exception:
    print('rb err', r2[:200], flush=True)

# 如果 fmt1 失败, 尝试格式 2: injectionRules (REST 文档格式)
if c != 200:
    body2 = {
        "mode": "custom",
        "allowedDomains": ["httpbin.org", "*"],
        "injectionRules": [
            {"domain": "httpbin.org", "headers": {"Authorization": "Bearer INJMARK_9f31a2c7"}}
        ]
    }
    c, r = api('POST', '/v2/sandboxes/sessions/%s/network-policy?teamId=%s' % (sid, TEAM), body2)
    print('fmt2 injectionRules ->', c, r[:300], flush=True)
    time.sleep(2)

# 验证: 沙箱内 curl httpbin.org/anything (正常路径, 应看到注入 header)
c3, r3 = cmd(sid, 'sh', ['-c', 'curl -sk --max-time 10 https://httpbin.org/anything 2>&1 | head -40'], timeout_ms=30000)
print('=== curl httpbin /anything ->', c3, flush=True)
print(r3[:1500], flush=True)

print('=== T1 DONE ===', flush=True)
