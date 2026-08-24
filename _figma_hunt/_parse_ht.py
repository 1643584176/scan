# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding=utf-8, errors=replace)
d = json.load(open('_gql_figma_ht.json', encoding='utf-8'))
print('total:', d.get('data',{}).get('search',{}).get('total_count'))
nodes = d.get('data',{}).get('search',{}).get('nodes',[])
print('nodes:', len(nodes))
for n in nodes:
    r = n.get('report') or {}
    title = (r.get('title') or '?')[:100]
    print('-', n.get('reporter',{}).get('username'), '|', title, '|', r.get('state'), '| sev:', r.get('severity_rating'), '|', (r.get('latest_disclosable_activity_at') or '')[:10])
