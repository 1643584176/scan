# -*- coding: utf-8 -*-
"""h1x50e: GET /bugs?subject= 匿名基线(401/302/200 差异;subject=user vs team handle)
数据端点确认:/bugs?params 在 XHR 下返回 JSON?"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})

BASE = 'https://hackerone.com/bugs?subject=%s&report_id=0&view=open&substates%%5B%%5D=new&substates%%5B%%5D=triaged&text_query=&sort_type=latest_activity&sort_direction=descending&limit=25&page=1'

def probe(name, url, hdrs=None):
    try:
        r = s.get(url, headers=hdrs or {}, timeout=15, allow_redirects=False)
        ct = r.headers.get('content-type', '')[:40]
        body = r.text[:200].replace('\n', ' ')
        print(f'--- {name} [{r.status_code}] ct={ct} loc={r.headers.get("location","")[:80]}')
        print(f'    {body}')
    except Exception as e:
        print(f'--- {name} ERR {type(e).__name__}: {e}')

for subj in ['user', 'neon_bbp', 'security', '']:
    probe('anon_subj=%r plain' % subj, BASE % subj)
    probe('anon_subj=%r xhr' % subj, BASE % subj, {'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json'})
