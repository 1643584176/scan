# -*- coding: utf-8 -*-
"""h1x30: 公开报告 .json 的 attachments 结构(找附件 URL 形态/可枚举性)"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()

s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})

for rid in ['3973228', '2696294', '2487889']:
    try:
        r = s.get(f'https://hackerone.com/reports/{rid}.json', timeout=20)
        if r.status_code != 200:
            print(f'[{rid}] status {r.status_code}')
            continue
        j = r.json()
        att = j.get('attachments', [])
        print(f'[{rid}] title={j.get("title","")[:70]} attachments={len(att)}')
        for a in att[:5]:
            if isinstance(a, dict):
                print('   keys:', list(a.keys()))
                print('   ', json.dumps(a, ensure_ascii=False)[:500])
            else:
                print('   raw:', str(a)[:500])
    except Exception as e:
        print(f'[{rid}] ERR {e}')
    print()
