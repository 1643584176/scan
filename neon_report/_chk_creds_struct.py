# -*- coding: utf-8 -*-
"""只读检查:控制面凭据文件字段结构(打码),不打印任何 secret"""
import json, ast

d = json.load(open(r'D:\scan\neon_report\_apikey.json', encoding='utf-8'))
print('_apikey.json keys:', list(d.keys()))
for k, v in d.items():
    if isinstance(v, str) and len(v) > 10:
        print('  %s = str(len=%d) head=%s' % (k, len(v), v[:10]))
    else:
        print('  %s = %r' % (k, v))

src = open(r'D:\scan\neon_report\_neon_creds_stage.py', encoding='utf-8').read()
# 仅打印变量名与类型(值打码)
mod = ast.parse(src)
for node in mod.body:
    if isinstance(node, ast.Assign):
        for t in node.targets:
            if isinstance(t, ast.Name):
                v = node.value
                if isinstance(v, ast.Constant) and isinstance(v.value, str):
                    s = v.value
                    print('creds var %s = str(len=%d) head=%s' % (t.id, len(s), s[:12]))
                else:
                    print('creds var %s = %s' % (t.id, type(v).__name__))
    elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        print('creds var %s (annotated)' % node.target.id)
