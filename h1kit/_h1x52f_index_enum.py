# -*- coding: utf-8 -*-
"""h1x52f: 枚举 search index 名(匿名只读,报错=不存在,total_count=存在)"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})

names = [
    'CompleteHacktivityReportIndex',   # 已知有效
    'HacktivityReportIndex', 'HacktivityIndex', 'Hacktivity',
    'ReportIndex', 'ReportsIndex', 'AllReportsIndex', 'CompleteReportIndex', 'Report',
    'NotificationIndex', 'NotificationsIndex', 'Notification',
    'OpportunityIndex', 'OpportunitiesIndex', 'Opportunity',
    'FindingIndex', 'FindingsIndex', 'Finding',
    'AssetIndex', 'AssetsIndex', 'StructuredScopeIndex', 'AssetDocumentIndex',
    'OrganizationMemberIndex', 'StoredQueryIndex', 'DocumentIndex',
    'SearchIndex', 'Index', 'All', 'CompleteIndex', 'GatewayIndex',
]
for idx in names:
    q = '{ search(index: %s, query_string: "*", limit: 1) { total_count } }' % idx
    try:
        r = s.post('https://hackerone.com/graphql', json={'query': q}, timeout=15)
        t = r.text
        if '"total_count"' in t:
            try:
                tc = json.loads(t)['data']['search']['total_count']
                print('EXISTS %-38s total_count=%s' % (idx, tc))
            except Exception:
                print('EXISTS? %-38s %s' % (idx, t[:150]))
        elif 'Unknown index' in t or 'index' in t.lower():
            print('NO     %-38s %s' % (idx, t[:130].replace('\n', ' ')))
        else:
            print('??     %-38s %s' % (idx, t[:180].replace('\n', ' ')))
    except Exception as e:
        print('ERR    %-38s %s' % (idx, e))
