# -*- coding: utf-8 -*-
"""从搜索结果 dump 提取 content_id，看数值分布"""
import json, sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ids = []
for f in ('_r8_res_widget.json', '_r8_res_files.json', '_r10_desc_icon.json'):
    try:
        j = json.load(open(rf'D:\scan\figma_report\{f}', encoding='utf-8'))
        meta = j.get('meta') or {}
        res = meta.get('results') if isinstance(meta, dict) else None
        if isinstance(res, list):
            for it in res:
                m = it.get('model') or it
                cid = m.get('content_id') or m.get('id')
                if cid:
                    ids.append(str(cid))
    except Exception as e:
        print(f, 'err', e)

print(f'total ids: {len(ids)}')
for i in ids[:50]:
    print(i)
