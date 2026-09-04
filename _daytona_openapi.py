# -*- coding: utf-8 -*-
"""Daytona OpenAPI spec 分析:提取全部路径、方法、认证要求、参数"""
import json, re
from collections import Counter

SRC = r'C:\Users\tndc2\.qoder\cache\projects\scan-72ece876\agent-tools\0cd3bdc9\ffe1db22.txt'

with open(SRC, encoding='utf-8') as f:
    content = f.read()

# WebFetch 可能包了 markdown 代码块,剥离
if content.lstrip().startswith('{'):
    spec = json.loads(content)
else:
    m = re.search(r'```json\s*(\{.*?\})\s*```', content, re.S)
    if m:
        spec = json.loads(m.group(1))
    else:
        # 找第一个 { 到最后一个 }
        start = content.find('{')
        end = content.rfind('}')
        spec = json.loads(content[start:end+1])

paths = spec.get('paths', {})
print('TOTAL PATHS: %d' % len(paths))

# 按前缀分组
groups = Counter()
for p in paths:
    seg = p.strip('/').split('/')
    groups['/' + seg[0] if seg else '/'] += 1

print('\n=== 按一级前缀分组 ===')
for g, c in groups.most_common():
    print('%-20s %d' % (g, c))

# 输出完整路径列表(方法)
print('\n=== 全部端点 ===')
for p in sorted(paths):
    methods = ','.join(m.upper() for m in paths[p] if m in ('get','post','put','delete','patch'))
    print('%-8s %s' % (methods, p))

# 认证方式
print('\n=== 安全方案 ===')
print(json.dumps(spec.get('components', {}).get('securitySchemes', {}), indent=1)[:2000])
