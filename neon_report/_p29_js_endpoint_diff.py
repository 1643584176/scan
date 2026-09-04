# -*- coding: utf-8 -*-
"""JS bundle 全量端点提取 vs OpenAPI paths 差集:
1. 提取 app.js 所有 URL 字符串(/api/v1 /api/v2 字面量 + 模板拼接 + fetch/axios 调用)
2. 展开模板变量(常见前缀变量)
3. 与 _openapi_v2.json paths 求差 -> 新端点候选
"""
import re, os, json

here = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(here, '_js', 'app.js'), encoding='utf-8', errors='replace').read()
print('size:', len(src), flush=True)

# 1. 字面量端点(带 /api/ 或 api/v)
lit = set()
for m in re.finditer(r'["\'`]([^"\'`]{0,10}/api/v[12]/[^"\'`]{2,150})["\'`]', src):
    lit.add(m.group(1))
# 模板拼接: ".../xxx/${e}/yyy" 形态
tmpl = set()
for m in re.finditer(r'["\'`]([^"\'`]*?/api/v[12]/[^"\'`]*?\$\{[^}]{1,30}\}[^"\'`]{0,80})["\'`]', src):
    tmpl.add(m.group(1))
print('literal count:', len(lit), flush=True)
print('template count:', len(tmpl), flush=True)

# 2. 常见前缀变量: const X='/api/v2'; 拼 "/organizations/..." 
prefixes = set(re.findall(r'(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*["\'`](/api/v[12])["\'`]', src))
print('prefix vars:', prefixes, flush=True)
rest_lit = set()
for m in re.finditer(r'["\'`](/(?:organizations|projects|users|branches|endpoints|keys|roles|invites|members|transfers|connections|provisioning|agent|assistants|subscriptions|billing|audit|settings|tokens|webhooks|domains|authentication|auth|consumption|metrics|operations|databases|roles|permissions|features|products|plans|quotas|limits|integrations|oauth|sso|saml|scim|mcp)[^"\'`]{1,120})["\'`]', src):
    rest_lit.add(m.group(1))
print('rest literal count:', len(rest_lit), flush=True)

# 3. 全量 /api 附近抓 URL 段(宽松: 任意含 /api 或 api. 的字符串)
loose = set()
for m in re.finditer(r'["\'`]([^"\'`]{1,10}api[^"\'`]{2,160})["\'`]', src):
    s = m.group(1)
    if re.search(r'(organizations|projects|users|branches|keys|invites|transfer|agent|provision|mcp|assistant|connection|integration|subscription|billing|audit|webhook|sso|oauth|scim)', s):
        loose.add(s)
print('loose count:', len(loose), flush=True)

# OpenAPI paths 已知集合(尾段做模糊匹配)
d = json.load(open(os.path.join(here, '_openapi_v2.json'), encoding='utf-8'))
paths = set(d.get('paths', {}).keys())
print('\nOpenAPI paths:', len(paths), flush=True)

def norm(p):
    # /api/v2/organizations/{org_id}/members -> /organizations/{org_id}/members 形态用于对比
    p = re.sub(r'^/api/v[12]', '', p)
    p = re.sub(r'\{[^}]*\}', '{x}', p)
    return p

allcands = set()
for s in lit | tmpl:
    allcands.add(s)
for s in rest_lit:
    allcands.add('/api/v2' + s)
for s in loose:
    allcands.add(s)

print('\n=== 候选端点(总数 %d) ===' % len(allcands), flush=True)
cnt = 0
for s in sorted(allcands):
    # 去掉 query/变量残渣
    s2 = re.split(r'[?#]', s)[0]
    if not s2 or len(s2) < 12:
        continue
    # 规范化与 OpenAPI 对比
    n = norm(re.sub(r'\$\{[^}]*\}', '{x}', s2))
    known = any(norm(p) == n or norm(p).split('/')[1] == n.split('/')[1] and len(n.split('/')) == len(norm(p).split('/')) and n.split('/')[2:4] == norm(p).split('/')[2:4] for p in paths)
    if not known:
        print('NEW?', s2[:160], flush=True)
        cnt += 1
print('total new-like:', cnt, flush=True)
