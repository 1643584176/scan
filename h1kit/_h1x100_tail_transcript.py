# -*- coding: utf-8 -*-
"""读会话历史尾部,定位 CT1 浏览器块与用户最近消息(2026-09-09)"""
import json, io, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

P = r"C:\Users\tndc2\.qoder\cache\projects\scan-72ece876\conversation-history\c57b94b5\c57b94b5.jsonl"
lines = open(P, encoding="utf-8", errors="replace").read().splitlines()
print("total lines:", len(lines))

def txt_of(line):
    try:
        o = json.loads(line)
    except Exception:
        return None
    m = o.get("message", {})
    c = m.get("content")
    if isinstance(c, str):
        return ("user" if o.get("role") == "user" else "asst", c)
    if isinstance(c, list):
        out = []
        for it in c:
            if isinstance(it, dict) and it.get("type") == "text":
                out.append(it.get("text", ""))
        return ("user" if o.get("role") == "user" else "asst", "\n".join(out))
    return None

# 找最近 40 条非空文本
got = []
for ln in lines:
    t = txt_of(ln)
    if t and t[1].strip():
        got.append(t)

for role, text in got[-25:]:
    print("\n=====", role, "=====")
    print(text[:3000])
