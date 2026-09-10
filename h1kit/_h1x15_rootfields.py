# -*- coding: utf-8 -*-
"""h1x15: 提取所有 GraphQL query 的根选择集字段(顶层字段名)→ 未测根字段清单"""
import re, sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

t = open(r'D:\scan\h1kit\_h1x4_app.js', encoding='utf-8', errors='ignore').read()

# 字符串形式的 query 文档(可读性好)
queries = re.findall(r'"(?:\\n\s*)?(?:query|mutation)\s+([A-Za-z0-9_]+)\(([^"]*?)\)\s*\{([^"]+?)\}"', t)
print('total string queries:', len(queries))

roots = {}
for name, args, body in queries:
    # 顶层字段:body 里第一个 \n 前的内容(展开后第一行内的字段)
    body2 = body.replace('\\n', '\n')
    first_lines = body2.split('\n')
    # 找 '{' 之后的顶层字段(到嵌套 { 前或行尾)
    # 简化:第一行(去掉开头的 { )按空格拆字段名
    line0 = first_lines[0] if first_lines else ''
    # 提取形如 " field(...)..." 或 " field ..." 的 token
    toks = re.findall(r'([a-z_][a-z0-9_]*)(?:\(| |$)', line0.replace('{', ' '))
    for tk in toks:
        if tk in ('query', 'mutation', 'fragment', 'on'):
            continue
        roots.setdefault(tk, []).append(name)

print('\n=== ROOT FIELD -> queries ===')
for f, qs in sorted(roots.items()):
    print(f'{f:30s} {len(qs):4d}  ex:{qs[:3]}')
