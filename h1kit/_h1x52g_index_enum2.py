# -*- coding: utf-8 -*-
"""h1x52g: IndexEnum 完整枚举值 + 各索引匿名探测(匿名只读)"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})

q = '{ __type(name: "IndexEnum") { enumValues { name } } }'
r = s.post('https://hackerone.com/graphql', json={'query': q}, timeout=20)
print('=== IndexEnum 枚举值 ===')
print(r.text)
vals = [v['name'] for v in json.loads(r.text)['data']['__type']['enumValues']]
print('count:', len(vals))
print()

NODES = 'nodes { __typename }'
for idx in vals:
    q2 = '{ search(index: %s, query_string: "*", limit: 1) { total_count %s } }' % (idx, NODES)
    try:
        r2 = s.post('https://hackerone.com/graphql', json={'query': q2}, timeout=20)
        t2 = r2.text[:300].replace('\n', ' ')
        print('%-42s %s' % (idx, t2))
    except Exception as e:
        print('%-42s ERR %s' % (idx, e))
