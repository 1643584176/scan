# -*- coding: utf-8 -*-
"""从 chunk1037.js 提取全部 livegraph view 定义, 筛裸读候选
判定规则(对齐 DeveloperLinks zu 的特征):
  - 有 args 参数(可注入) 
  - fields 无 checkCanRead / 无 dZ(当前用户) / 无 permissionRequired
  - 输出候选定义片段供人工审计
"""
import re, sys, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

src = open("chunk1037.js", encoding="utf-8", errors="replace").read()

# 1. 注册表: ViewName:()=>var
reg = re.findall(r'([A-Za-z][A-Za-z0-9]*):\(\)=>([A-Za-z_$][A-Za-z0-9_$]*)', src)
print(f"registry: {len(reg)} entries")

# 2. 提取每个 var 的定义 (对象形式 {args:...} / function 形式)
defs = {}
for name, var in reg:
    # 对象定义: var={args:[...
    m = re.search(r'(?:const|var|let)?\s*' + re.escape(var) + r'\s*=\s*(\{args:\[)', src)
    if not m:
        continue
    start = m.start(1)
    # 括号配对截取完整对象
    depth = 0
    i = start
    n = len(src)
    while i < n:
        c = src[i]
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                break
        i += 1
    defs[name] = (var, src[start:i+1])

print(f"object-style view defs: {len(defs)}")

# 3. 分析特征
NO_PERM_MARK = ['checkCanRead', 'checkCanWrite', 'permissionRequired']
USER_BIND_MARK = ['(0,l.dZ)', 'getUserId', 'currentUser']

candidates = []
for name, (var, d) in defs.items():
    # args 参数名
    argnames = re.findall(r'name:"([^"]+)"', d.split('fields:')[0] if 'fields:' in d else d)
    if not argnames:
        continue
    # 权限特征
    has_perm = any(mk in d for mk in NO_PERM_MARK)
    has_ubind = any(mk in d for mk in USER_BIND_MARK)
    # 是否引用外部类型 (fields 里 nK 引用的)
    ext_refs = re.findall(r'nK\)\("([^"]+)"', d)
    # 危险豁免
    exempt = 'DangerouslyExempt' in d or 'Exempt' in d
    # 裸读候选: 无权限字段 + 无用户绑定 (外部引用不算, 可能引用带权限的类型, 单独列)
    if not has_perm and not has_ubind and not ext_refs:
        candidates.append((name, argnames, 'PURE-NOCHECK', exempt, d))
    elif not has_perm and not has_ubind and ext_refs:
        candidates.append((name, argnames, f'EXT-REF:{",".join(ext_refs[:3])}', exempt, d))

print(f"candidates: {len(candidates)}\n")
for name, argnames, kind, exempt, d in candidates:
    print(f"### {name} [{kind}] args={argnames} exempt={exempt}")
    print(d[:600])
    print()
