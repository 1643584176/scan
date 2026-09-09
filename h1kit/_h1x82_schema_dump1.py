# -*- coding: utf-8 -*-
"""schema 全量 dump(分页)——当源码审计(2026-09-09)"""
import json
import time
import urllib.request

BASE = "https://hackerone.com/graphql"
HDRS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Content-Type": "application/json"}

# 第一步:总类型数
def post(q, label):
    data = json.dumps({"query": q}).encode()
    req = urllib.request.Request(BASE, data=data, headers=HDRS)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8", "replace"))
        except Exception as e:
            print(label, "retry", attempt, e)
            time.sleep(3)
    return None

r = post("{ __schema { types { name } } }", "types")
names = [t["name"] for t in r["data"]["__schema"]["types"] if not t["name"].startswith("__")]
print("total types:", len(names))
with open(r"D:\scan\h1kit\_schema_type_names.json", "w") as f:
    json.dump(names, f)

# 类型名保存——下个脚本分批 dump 详情
