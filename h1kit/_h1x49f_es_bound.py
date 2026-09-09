# -*- coding: utf-8 -*-
"""h1x49f: hacktivity 索引内容边界验证(匿名只读)
对照:公开报告 2487889 元数据;验证 reporter/team/title 字段能否触达私有报告"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})

def search(name, qs, index='CompleteHacktivityReportIndex', timeout=20):
    q = '{ search(index: %s, query_string: "%s", limit: 1) { total_count } }' % (index, qs.replace('"', '\\"'))
    try:
        r = s.post('https://hackerone.com/graphql', json={'query': q}, timeout=timeout)
        print(f'--- {name} ---')
        print(f'  [{r.status_code}] {r.text[:250]}')
        return r.text
    except Exception as e:
        print(f'--- {name} ERR {type(e).__name__}: {e} ---')
        return None

# 1. 公开报告 2487889 元数据
r = s.get('https://hackerone.com/reports/2487889.json', timeout=20)
print('=== 2487889.json status', r.status_code, '===')
meta = {}
if r.status_code == 200:
    try:
        j = r.json()
        meta = {'title': j.get('title'), 'reporter': (j.get('reporter') or {}).get('username'),
                'team': (j.get('team') or {}).get('handle'), 'state': j.get('state')}
        print(json.dumps(meta, ensure_ascii=False)[:400])
    except Exception as e:
        print('json parse err', e, r.text[:200])
else:
    print(r.text[:150])

# 2. 用公开报告标题关键词搜索(验证 title 字段内容真实可检索)
t = meta.get('title') or ''
kw = t.split()[0][:20] if t else 'IDOR'
search('pub_title_kw', 'title:' + kw.replace(':', ''))

# 3. reporter 面
if meta.get('reporter'):
    search('pub_reporter', 'reporter:' + meta['reporter'])
search('self_reporter_xxbo', 'reporter:xxbo')
search('neon_hunter_xxbo', 'reporter:xxbo OR reporter:neon')  # 兜底

# 4. team 面
if meta.get('team'):
    search('pub_team', 'team:' + meta['team'])
search('team_neon', 'team:neon*')

# 5. substate/severity/disclosed 组合(看这些字段枚举值形态)
search('substate_triaged', 'substate:triaged')
search('sev_high', 'severity_rating:high')
search('sev_critical', 'severity_rating:critical')
search('sev_5', 'severity_rating:5')
search('disclosed_2024', 'disclosed_at:2024*')
