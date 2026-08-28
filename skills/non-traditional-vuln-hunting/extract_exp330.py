# -*- coding: utf-8 -*-
"""从 1a7a395a 提取 Vercel API 端点和 exp_j330 相关内容"""
import re, glob, os

BASE = r'C:\Users\tndc2\.qoder\cache\projects\scan-72ece876\conversation-history'
fp = os.path.join(BASE, '1a7a395a', '1a7a395a.jsonl')
with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# 1. 所有 URL
urls = set(re.findall(r'https?://[^\s"\'\\,)\]]+', content))
api_urls = sorted(u for u in urls if 'vercel' in u and ('api' in u or 'v1' in u or 'sandbox' in u))
print('=== API URL 候选 ===')
for u in api_urls[:25]:
    print(u[:180])

# 2. exp_j330 上下文
print('\n=== exp_j330 出现位置 ===')
for m in re.finditer(r'exp_j330', content):
    s = max(0, m.start() - 300)
    print(content[s:m.end() + 200].replace('\n', ' ')[:500])
    print('---')
