# -*- coding: utf-8 -*-
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
j = json.load(open(r'D:\scan\figma_report\_r14_versions.json', encoding='utf-8'))
pl = j['meta']['plugin']
print('plugin keys:', list(pl.keys()))
print()
vs = pl.get('versions')
if isinstance(vs, dict):
    print(f'versions count: {len(vs)}')
    for vid, v in vs.items():
        print(f'--- version {vid} ---')
        for k, vv in v.items():
            s = json.dumps(vv, ensure_ascii=False) if isinstance(vv, (dict, list)) else str(vv)
            print(f'    {k}: {s[:200]}')
else:
    print('versions type:', type(vs).__name__)
    print(json.dumps(vs, ensure_ascii=False)[:1500])
print()
# plugin 全字段
print('=== plugin other fields ===')
for k, vv in pl.items():
    if k == 'versions':
        continue
    s = json.dumps(vv, ensure_ascii=False) if isinstance(vv, (dict, list)) else str(vv)
    print(f'  {k}: {s[:220]}')
