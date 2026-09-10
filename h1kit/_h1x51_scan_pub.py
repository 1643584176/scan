# -*- coding: utf-8 -*-
"""h1x51: 扫描公开 hacktivity 中 hackerone.com 平台相关越权披露报告(匿名只读)
目标:定位用户所说"只有标题"的越权报告,拿 id/标题清单供后续 .json 全文抓取"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})

NODES = '''nodes { ... on HacktivityDocument { id report { id title } reporter { username } team { handle } disclosed_at submitted_at } }'''

def search(name, qs, limit=25, index='CompleteHacktivityReportIndex', timeout=25):
    q = 'query { search(index: %s, query_string: "%s", limit: %d) { total_count %s } }' % (index, qs.replace('"', '\\"'), limit, NODES)
    try:
        r = s.post('https://hackerone.com/graphql', json={'query': q}, timeout=timeout)
        t = r.text
        print(f'--- {name} ---')
        try:
            j = r.json()
            if 'errors' in j:
                print('  GQL_ERR:', json.dumps(j['errors'])[:400])
            else:
                sc = j['data']['search']
                print(f"  total={sc['total_count']} nodes={len(sc.get('nodes') or [])}")
                for n in sc.get('nodes') or []:
                    rp = n.get('report') or {}
                    print(f"  #{rp.get('id')} {str(rp.get('title'))[:90]} | rep={ (n.get('reporter') or {}).get('username') } team={(n.get('team') or {}).get('handle')} disclosed={n.get('disclosed_at')} submitted={n.get('submitted_at')}")
        except Exception as e:
            print('  PARSE_ERR', e, t[:200])
        return r.text
    except Exception as e:
        print(f'--- {name} ERR {type(e).__name__}: {e} ---')
        return None

# 1. H1 自家 team(security id=13 / HackerOne)全部报告节点
search('h1_team_all', 'team:HackerOne', 25)
# 2. H1 自家 越权关键词
search('h1_idor', '(title:IDOR OR title:"insecure direct" OR title:unauthorized OR title:"access control") AND team:HackerOne', 25)
# 3. 平台自身(标题含 hackerone.com)越权类
search('h1com_idor', '(title:hackerone.com OR title:hackerone) AND (title:IDOR OR title:unauthorized OR title:private OR title:access)', 25)
# 4. 平台自身 标题含 hackerone.com 全量
search('h1com_all', 'title:hackerone.com', 25)
# 5. 2026 年披露的 H1 自家报告(最近披露线索)
search('h1_2026', 'team:HackerOne AND disclosed_at:2026*', 25)
