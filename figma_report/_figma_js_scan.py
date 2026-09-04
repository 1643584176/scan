# -*- coding: utf-8 -*-
"""Figma JS 静态分析:搜索认证/livegraph/端点关键词"""
import os, re

D = 'D:/scan/figma_report/_js/'
files = [f for f in os.listdir(D) if f.endswith('.js')]
print('js files:', len(files))

# 关键词 -> 命中文件与上下文
PATS = {
    'livegraph': re.compile(r'livegraph'),
    'ph_param': re.compile(r'[\"\']ph[\"\']\s*[:=]|ph\s*[:=]'),
    'x-figma-token': re.compile(r'x-figma-token', re.I),
    'x-figma-user': re.compile(r'x-figma-user-id', re.I),
    'auth_token': re.compile(r'XAuthToken|x-auth-token|authToken', re.I),
    'session_token': re.compile(r'sessionToken|session_token|figma_uid|figma_session', re.I),
    'hmac': re.compile(r'HMAC|hmac|subtle\.sign|signAsync', re.I),
    'realtime_token': re.compile(r'realtime_token|realtimeToken', re.I),
}

for name, pat in PATS.items():
    print('\n==== %s ====' % name)
    hits = 0
    for fn in sorted(files):
        p = os.path.join(D, fn)
        try:
            with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception:
            continue
        for m in pat.finditer(content):
            hits += 1
            if hits <= 3:
                s = max(0, m.start() - 100)
                e = min(len(content), m.end() + 150)
                print('  [%s]' % fn)
                print('    ...%s...' % content[s:e].replace('\n', ' ')[:250])
    print('  total hits: %d' % hits)
