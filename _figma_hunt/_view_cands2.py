# -*- coding: utf-8 -*-
"""重新解析 lg_view_scan_out.txt：全量 view 候选筛选，输出参数需求分类表"""
import re, json, sys

SRC = r'D:\scan\_figma_hunt\lg_view_scan_out.txt'
text = open(SRC, encoding='utf-8', errors='replace').read()
lines = text.split('\n')

# 分块：### 行开始，直到下一个 ###
blocks = []
cur = None
for l in lines:
    if l.startswith('### '):
        if cur: blocks.append(cur)
        cur = {'header': l, 'body': []}
    elif cur is not None:
        cur['body'].append(l)
if cur: blocks.append(cur)
print(f'view 块总数: {len(blocks)}')

def parse_args(args_str):
    """解析 args 列表 -> [(name, kind)]（header 只有名字，类型从 body JSON 补）"""
    out = []
    for m in re.finditer(r'\{name:"(\w+)",type:\{kind:"(\w+)"\}', args_str):
        out.append((m.group(1), m.group(2)))
    return out

name_m = None

def find_root_filter(fields_str):
    """fields: 后第一个 { ... } 到 ,{ 或 ] 或 结束"""
    m = re.search(r'fields:\{(.*)$', fields_str, re.S)
    if not m: return ''
    s = m.group(1)
    # 找到第一个 { 开始的对象，到匹配的嵌套结束
    depth = 0
    for i, ch in enumerate(s):
        if ch == '{':
            depth += 1
            if depth == 1: start = i
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return s[start:i+1]
    return s[:300]

results = []
for b in blocks:
    header = b['header']
    body = '\n'.join(b['body'])
    name_m = re.match(r'### (\w+)', header)
    if not name_m: continue
    name = name_m.group(1)
    tag_m = re.search(r'\[(PURE|EXT:[^\]]+)\]', header)
    tag = tag_m.group(1) if tag_m else ''
    args_m = re.search(r"args=\[(.*?)\]", header)
    args_str = args_m.group(1) if args_m else ''
    # header 里只有名字
    hdr_args = re.findall(r"'(\w+)'", args_str)
    # body 定义 JSON 里的类型
    body_args = parse_args(body)
    if body_args:
        args = body_args
    else:
        args = [(a, '') for a in hdr_args]
    # 定义体里的 fields
    root = find_root_filter(body)
    # dZ 绑定检测（当前用户）
    has_dz = bool(re.search(r'dZ\)?"?\(?"userId"', root))
    # WY 透传参数检测
    wy_params = re.findall(r'(\w+):WY\)?\("([^"]+)"\)', root)
    if not wy_params:
        wy_params = re.findall(r'(\w+):WY\("([^"]+)"\)', root)
    results.append({
        'name': name, 'tag': tag, 'args': args, 'root': root,
        'has_dz': has_dz, 'wy': wy_params
    })

print(f'解析成功: {len(results)} 个')

# 候选：根 filter 无 dZ 绑定
cands = [r for r in results if not r['has_dz']]
print(f'\n===== 根 filter 无 dZ 绑定候选: {len(cands)} =====\n')

def classify(r):
    # 参数类型分布：优先按字段名
    argnames = [a[0] for a in r['args']]
    for a in argnames:
        al = a.lower()
        if 'filekey' in al: return 'fileKey'
        if 'projectid' in al: return 'projectId'
        if 'teamid' in al: return 'teamId'
        if 'userid' in al or al == 'ownerid': return 'userId'
        if 'workspaceid' in al: return 'workspaceId'
        if 'planid' in al or 'plantype' in al: return 'plan'
        if 'requestid' in al: return 'requestId'
        if 'commentid' in al or 'threadid' in al: return 'commentId'
        if 'orgid' in al: return 'orgId'
    # 有 uuid 类型的
    for a in r['args']:
        if a[1] == 'uuid': return 'uuid'
    if not r['args']: return 'no-args'
    return 'other'

from collections import Counter
by_type = Counter(classify(r) for r in cands)
print('分类分布:', dict(by_type))
print()

# 输出：类别 + view 名 + args + 返回里是否有敏感字段（email/name/url）
SENS = re.compile(r'email|invitee|phone|address|billing|payment|private|secret|token|credit|password', re.I)
for ctype in ['fileKey', 'projectId', 'teamId', 'userId', 'workspaceId', 'commentId', 'plan', 'requestId', 'uuid', 'orgId', 'no-args', 'other']:
    group = [r for r in cands if classify(r) == ctype]
    if not group: continue
    print(f'--- {ctype} ({len(group)}) ---')
    for r in group:
        sens = 'SENS!' if SENS.search(r['root']) else ''
        print(f"  {r['name']:55s} {r['tag']:20s} args={[a[0] for a in r['args']]} wy={r['wy']} {sens}")
    print()
