# -*- coding: utf-8 -*-
"""h1x52p: ReportDuplicateInformation/DeduplicationActionRecommendation/DupeWindow + deduplication_recommendations 深层类型"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})

def probe(name, q, cut=4000):
    r = s.post('https://hackerone.com/graphql', json={'query': q}, timeout=20)
    print(f'--- {name} [{r.status_code}]')
    print(r.text[:cut].replace('\n', ' '))
    print()

for tn in ['ReportDuplicateInformation', 'DeduplicationActionRecommendation', 'DupeWindow']:
    probe('type_' + tn, '''query { __type(name: "%s") { kind fields { name type { kind name ofType { kind name ofType { kind name } } } } } }''' % tn)
# deduplication_recommendations 的 List 元素类型
probe('dedup_rec_list', '''query { __type(name: "Report") { fields { name type { kind ofType { kind ofType { kind name ofType { kind name } } } } } } }''', 300)
