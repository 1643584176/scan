# -*- coding: utf-8 -*-
"""T1h:命中详情 + 精确短语验证(2026-09-08,匿名)"""
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
        print(f"== {label}: {r.text[:3000]}")
    except Exception as e:
        print(f"== {label} ERR {e}")

# 1. cloud_admin superuser 3 条详情(是否含我们的报告)
gql('{ search(index: %s, query_string: "cloud_admin superuser", first: 5){ total_count edges{ node{ ... on HacktivityDocument{ id public disclosed submitted_at report{ id title substate } team{ handle } } } } } }' % IDX, "doc_ca")
time.sleep(0.5)

# 2. 精确短语(我们的完整标题词)
for i, q in enumerate(['"Tenant to cloud_admin superuser"', '"arbitrary file read/write on the compute"',
                       '"enabling arbitrary file read/write"', '"repack.log"']):
    gql('{ search(index: %s, query_string: %s, first: 1){ total_count } }' % (IDX, json.dumps(q)), "exact_%d" % i)
    time.sleep(0.4)
