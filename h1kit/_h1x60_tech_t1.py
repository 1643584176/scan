# -*- coding: utf-8 -*-
"""T1:hacktivity 搜索查询的排序/过滤参数类型盘点(2026-09-08,匿名)"""
import requests
import json

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
S = requests.Session()
S.headers.update({"User-Agent": UA})

# 1. 匿名 /graphql 可达性:hacktivity 查询
q1 = """{ hacktivity(first:3){ edges{ node{ __typename } } } }"""
try:
    r = S.post("https://hackerone.com/graphql", json={"query": q1}, timeout=15)
    print("== anon hacktivity:", r.status_code, r.text[:300])
except Exception as e:
    print("ERR", e)

# 2. introspect:hacktivity 查询字段的 args(找 String 型 sort/order/filter)
q2 = """{ __type(name:"Query"){ fields{ name args{ name type{ kind name ofType{ kind name ofType{ kind name ofType{ kind name } } } } } } } }"""
try:
    r = S.post("https://hackerone.com/graphql", json={"query": q2}, timeout=15)
    j = r.json()
    if "data" in j and j["data"] and j["data"].get("__type"):
        for f in j["data"]["__type"]["fields"]:
            if f["name"] in ("hacktivity", "search", "hacktivity_articles", "hacktivity_query"):
                print("== field", f["name"], json.dumps(f["args"], ensure_ascii=False)[:1500])
    else:
        print("== introspect response:", r.text[:300])
except Exception as e:
    print("ERR2", e)

# 3. batch body 探测(GraphQL 引擎 batch 支持?)
try:
    r = S.post("https://hackerone.com/graphql",
               json=[{"query": "{ me { id } }"}, {"query": "{ hacktivity(first:1){ edges{ node{ __typename } } } }"}],
               timeout=15)
    print("== batch:", r.status_code, r.text[:300])
except Exception as e:
    print("ERR3", e)

# 4. APQ 探测(extensions.persistedQuery)
try:
    r = S.post("https://hackerone.com/graphql",
               json={"query": "", "extensions": {"persistedQuery": {"version": 1, "sha256Hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}}},
               timeout=15)
    print("== APQ:", r.status_code, r.text[:300])
except Exception as e:
    print("ERR4", e)
