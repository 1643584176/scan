# -*- coding: utf-8 -*-
"""T1b:search 的 SortInput/QueryInput/IndexEnum 结构(2026-09-08,匿名)"""
import requests
import json

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
S = requests.Session()
S.headers.update({"User-Agent": UA})

def gql(query, label):
    try:
        r = S.post("https://hackerone.com/graphql", json={"query": query}, timeout=20)
        j = r.json()
        s = json.dumps(j, ensure_ascii=False)
        print(f"== {label}: {r.status_code} {s[:2500]}")
        return j
    except Exception as e:
        print(f"== {label} ERR {e}")
        return None

# 1. SortInput/QueryInput 字段 + IndexEnum 值
gql("""{ a:__type(name:"SortInput"){ name inputFields{ name type{ kind name ofType{ kind name ofType{ kind name } } } } },
b:__type(name:"QueryInput"){ name inputFields{ name type{ kind name ofType{ kind name ofType{ kind name } } } } },
c:__type(name:"IndexEnum"){ name enumValues{ name } } }""", "types")

# 2. 试最小 search 查询(拿正确调用形态)
gql("""{ search(index:REPORT, query_string:"hackerone", first:2){ total_count edges{ node{ __typename } } } }""", "search_min")

# 3. query_string 特殊字符探测(ES 语法错误/行为差异)
for i, qs in enumerate(["\"", "\\", "{", "}", "*:*", "\" OR \"", "a]b", "&&"]):
    gql('{ s%d: search(index:REPORT, query_string:%s, first:1){ total_count } }' % (i, json.dumps(qs)), "qs_%d_%r" % (i, qs[:6]))
