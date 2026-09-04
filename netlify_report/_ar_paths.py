# -*- coding: utf-8 -*-
"""Agent Runner 相关 API 路径与调用上下文"""
import re

data = open(r'D:\scan\netlify_report\_js\net_app.js', encoding='utf-8', errors='ignore').read()

# agent runner 相关 URL 片段
paths = sorted(set(re.findall(r'/(?:api/v1/)?[A-Za-z0-9_\-]*(?:agent[_-]?runner|agentRunner)[A-Za-z0-9_\-/{}]*', data)))
print('== agent runner 路径 ==')
for p in paths:
    print(' ', p)

# agentRunnerSession 等 queryKey 上下文
for kw in ['agentRunnerSession', 'agent-runner-session', 'sessions', 'agent-runner']:
    hits = [m.start() for m in re.finditer(re.escape(kw), data)]
    if hits:
        print('\n== %s (%d) ==' % (kw, len(hits)))
        for i in hits[:3]:
            print('...%s...' % data[max(0, i - 400):i + 400].replace('\n', ' '))
            print()
