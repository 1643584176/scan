# -*- coding: utf-8 -*-
"""解析 probe7:lambda-events 上下文 + 路径常量"""
import json

d = json.load(open(r'D:\scan\netlify_report\_probe7_out.json', encoding='utf-8'))
print('=== ctx(lambda-events 上下文)===')
for c in d.get('ctx', []):
    print('---')
    print(c[:850])
print()
print('=== paths ===')
for p in d.get('paths', []):
    print(' ', p)
print()
print('=== eventRefs ===')
for e in d.get('eventRefs', [])[:60]:
    print(' ', e[:150])
print()
print('=== postRefs ===')
for p in d.get('postRefs', [])[:30]:
    print(' ', p[:150])
