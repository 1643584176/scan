# -*- coding: utf-8 -*-
"""agentic_provisioning 全端点 + 创建流程 + orchestrator 枚举"""
import re

t = open('D:/scan/neon_report/_js/app.js', encoding='utf-8', errors='ignore').read()

# 所有 agentic/account_request/orchestrator 相关片段
for kw in ['agentic_provisioning', 'account_requests', 'orchestrator', 'AgenticProvision']:
    idxs = [m.start() for m in re.finditer(re.escape(kw), t)]
    print('=== %s: %d hits ===' % (kw, len(idxs)))

# 提取该功能附近所有 API 调用(fetch 模板)
seg = []
for m in re.finditer(r'agentic_provisioning[^"\'`]{0,120}', t):
    s = m.start()
    seg.append(t[max(0, s - 300):s + 200])
seen = set()
for s in seg:
    # 找 URL 模板
    for mm in re.finditer(r'["\'`](/api/v2/[a-zA-Z0-9_\-/${}.]+)["\'`]', s):
        u = mm.group(1)
        if u not in seen:
            seen.add(u)
            print('URL:', u)
