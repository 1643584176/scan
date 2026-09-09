# -*- coding: utf-8 -*-
"""h1x18: AST 解析所有 OperationDefinition 的顶层字段(权威根字段清单)"""
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

t = open(r'D:\scan\h1kit\_h1x4_app.js', encoding='utf-8', errors='ignore').read()

# 定位 OperationDefinition 开头的变量赋值 / 字典值
# 形态: {kind:`OperationDefinition`,operation:`query`,name:{kind:`Name`,value:`X`},variableDefinitions:[...],selectionSet:{kind:`SelectionSet`,selections:[...]}
op_pat = re.compile(r'\{kind:`OperationDefinition`,operation:`(query|mutation)`,name:\{kind:`Name`,value:`([A-Za-z0-9_]+)`\}')
# 找顶层 selections 数组:在 OperationDefinition 对象内部第一个 'selectionSet:{kind:`SelectionSet`,selections:['

def balanced_end(s, start, open_ch, close_ch):
    depth = 0
    for i in range(start, len(s)):
        c = s[i]
        if c == open_ch: depth += 1
        elif c == close_ch:
            depth -= 1
            if depth == 0:
                return i
    return -1

roots = {}
n = 0
for m in op_pat.finditer(t):
    op_type, op_name = m.group(1), m.group(2)
    # 在 op 对象范围内找 selections 数组(取 op 起点后 200KB 内,防止跨对象)
    start = m.start()
    sel_marker = 'selectionSet:{kind:`SelectionSet`,selections:['
    si = t.find(sel_marker, start, start + 200000)
    if si == -1:
        continue
    arr_start = si + len(sel_marker) - 1  # 指向 '['
    # 数组结束:数方括号
    end = balanced_end(t, arr_start, '[', ']')
    if end == -1:
        continue
    arr_body = t[arr_start+1:end]
    n += 1
    # 提取顶层元素(逐个大括号配平)
    fields = []
    i = 0
    while i < len(arr_body):
        if arr_body[i] == '{':
            e = balanced_end(arr_body, i, '{', '}')
            if e == -1: break
            el = arr_body[i+1:e]
            fm = re.match(r'kind:`Field`,name:\{kind:`Name`,value:`([A-Za-z0-9_]+)`\}', el)
            if fm:
                fields.append(fm.group(1))
            i = e + 1
        else:
            i += 1
    for f in fields:
        roots.setdefault(f, set()).add((op_type, op_name))

print('operations parsed:', n)
print()
for f, qs in sorted(roots.items(), key=lambda x: -len(x[1])):
    ql = sorted(qs)
    print(f'{f:35s} {len(ql):4d}  {ql[:5]}')
