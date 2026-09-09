# -*- coding: utf-8 -*-
"""h1x52t: bundle 考古 report_intent 前端使用 + 匿名小样本探测 intent id 空间(只读,慢速)"""
import re, sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()

t = open(r'D:\scan\h1kit\_h1x4_app.js', encoding='utf-8', errors='ignore').read()
print('===== bundle: report_intent =====')
cnt = 0
for m in re.finditer(r'report_intent', t):
    j = m.start()
    print('=' * 12, '@', j)
    print(t[max(0, j-400):j+500].replace('\n', ' ')[:900])
    cnt += 1
    if cnt >= 6:
        break

print()
print('===== 探测 report_intent(id) =====')
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})

def probe(iid, tag):
    try:
        r = s.post('https://hackerone.com/graphql', json={'query': 'query { report_intent(id: %d) { id _id title state report { id title } team { handle } created_at } }' % iid}, timeout=15)
        print(tag, iid, '->', r.text[:400].replace('\n', ' '))
    except Exception as e:
        print(tag, iid, 'ERR', e)

# 低位密集 1-25
for i in range(1, 26):
    probe(i, 'low')
    time.sleep(0.4)
# 大位点采样
for i in [1000, 10000, 100000, 500000, 1000000, 2000000, 3732660, 3992341, 4000000]:
    probe(i, 'sample')
    time.sleep(0.4)
