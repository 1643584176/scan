# -*- coding: utf-8 -*-
"""解析 AL2 输出:找带 email 字面量参数的端点
用法:把浏览器 AL2 结果(JSON)存到文件再跑
"""
import json
import sys

data = json.load(open(sys.argv[1], encoding="utf-8"))
res = {}
for k in ("a", "b"):
    q = data["data"][k]
    fs = q["fields"]
    hits = [f["name"] for f in fs if any("email" in a["name"].lower() for a in f["args"])]
    res[k] = hits
print(json.dumps(res, indent=1))
