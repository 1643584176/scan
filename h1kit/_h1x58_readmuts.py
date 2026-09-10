# -*- coding: utf-8 -*-
"""753 mutation 文档串读取型筛选(2026-09-08)
找 bundle 中前端真实调用的、名字含读取语义或返回 Report 内容字段的 mutation
"""
import re

with open(r"D:\scan\h1kit\_h1x4_app.js", "r", encoding="utf-8", errors="replace") as f:
    data = f.read()

# 1. 文档字符串形态:mutation Name(...) { ... }
doc_muts = re.findall(r"mutation\s+([A-Za-z0-9_]+)\s*(\([^)]{0,400}?\))?\s*\{", data)
print("== 文档串形态 mutation 名:", len(doc_muts))

# 2. AST 形态:operation:`mutation`,name:{kind:`Name`,value:`X`}
ast_muts = re.findall(r"operation:`mutation`,name:\{kind:`Name`,value:`([A-Za-z0-9_]+)`\}", data)
print("== AST 形态 mutation 名:", len(ast_muts))

names = sorted(set(m for m, _ in doc_muts) | set(ast_muts))
print("== 去重总数:", len(names))

# 3. 读取语义关键词
READ_KW = ["view", "read", "get", "fetch", "load", "export", "download", "show", "open",
           "mark", "seen", "watched", "acknowledge", "print", "preview", "snapshot", "retrieve"]
hits = [n for n in names if any(k in n.lower() for k in READ_KW)]
print("== 读取语义名:", len(hits))
for h in sorted(hits):
    print("   ", h)

# 4. 对每个 mutation 名,抓它附近 600 字符上下文,标注是否含 Report 内容字段
CONTENT_FIELDS = ["vulnerability_information", "activities", "comments", "content", "details",
                  "title", "severity", "attachment", "internal", "body", "summary"]
print("\n== 含内容字段上下文的 mutation(名字含读取语义):")
for h in sorted(hits):
    for m in re.finditer(re.escape(h), data):
        ctx = data[max(0, m.start() - 50):m.start() + 700]
        found = [c for c in CONTENT_FIELDS if c in ctx]
        if found:
            snippet = ctx[:400].replace("\n", " ")
            print(f"\n--- {h} [fields: {found}]")
            print(snippet[:350])
            break  # 只打第一个上下文

# 5. 全部含 vulnerability_information 的 mutation 上下文(不看名字)
print("\n== 上下文含 vulnerability_information 的 mutation 名:")
for m in re.finditer(r"vulnerability_information", data):
    back = data[max(0, m.start() - 800):m.start()]
    mm = re.findall(r"(?:mutation\s+|value:`)([A-Za-z0-9_]{3,60})`?(?:\s*\()?", back)
    if mm:
        print("   ", mm[-1])
