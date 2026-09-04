# -*- coding: utf-8 -*-
"""INITIAL_OPTIONS 中 B 的 org_id/team 等上下文字段 + user_data 完整"""
import json, re

c = open('D:/scan/figma_report/_js/app_file_b.html', 'r', encoding='utf-8', errors='ignore').read()
scripts = re.findall(r'<script(?![^>]*src)[^>]*>(.*?)</script>', c, re.S)
data = None
for s in scripts:
    if 'INITIAL_OPTIONS' in s and 'EARLY_ARGS' in s:
        try:
            data = json.loads(s)
            break
        except Exception:
            pass
if data is None:
    for s in scripts:
        if 'INITIAL_OPTIONS' in s:
            try:
                data = json.loads(s)
                break
            except Exception:
                pass

if data:
    io = data.get('INITIAL_OPTIONS', data if 'INITIAL_OPTIONS' in data else {})
    if 'INITIAL_OPTIONS' in data:
        io = data['INITIAL_OPTIONS']
    print('user_data:', json.dumps(io.get('user_data'), ensure_ascii=False)[:600])
    print()
    for k in ['org_id', 'team_id', 'editing_file', 'user_ip', 'account_picker_data']:
        if k in io:
            print(k, ':', json.dumps(io[k], ensure_ascii=False)[:800])
            print()
else:
    print('parse failed')
