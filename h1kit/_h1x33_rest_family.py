# -*- coding: utf-8 -*-
"""h1x33: 旧版表单端点家族存活探测(匿名;401=活/404=无)
目标:2024 bugs.json IDOR 的同族端点是否漏修(登录态可再测 organization_id/text_query)"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()

s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36'})

candidates = [
    '/bugs.json',            # 2024 IDOR 修复目标(基线:401)
    '/reports.json',
    '/hacktivity.json',
    '/notifications.json',
    '/programs.json',
    '/users.json',
    '/report_requests.json',
    '/opportunities.json',
    '/retests.json',
    '/teams.json',
    '/bounties.json',
    '/invitations.json',
    '/comments.json',
    '/activities.json',
    '/search.json',
    '/attack_surface.json',
]
for p in candidates:
    url = 'https://hackerone.com' + p
    try:
        r = s.get(url, timeout=15, allow_redirects=False)
        ct = r.headers.get('content-type', '')[:40]
        body = r.text[:120].replace('\n', ' ')
        print(f'[{r.status_code}] {p} ct={ct} body={body}')
    except Exception as e:
        print(f'[ERR] {p} {e}')
