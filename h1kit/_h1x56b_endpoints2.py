# -*- coding: utf-8 -*-
"""h1x56b: bundle 全量端点提取v2 - 含模板${}的相对URL,去静态/已测"""
import io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
data = open(r'D:\scan\h1kit\_h1x4_app.js', encoding='utf-8', errors='replace').read()

# 所有 fetch/请求封装的字面量+模板串(允许 ${} 与转义)
pat = re.compile(r'''fetch\([`"]([^`"]{1,300})[`"]''')
f1 = pat.findall(data)
# 更宽:找所有 `相对路径` 反引号串(前文常见 Backbone url / 模板)
f2 = re.findall(r'[`"](/[A-Za-z0-9_${}./?=&%:-]{1,200})[`"]', data)

allu = set(f1) | set(f2)
print('total url-ish:', len(allu))
out = []
for u in sorted(allu):
    if u.startswith(('/assets', '/static', '/graphql', '//')):
        continue
    if '.svg' in u or '.png' in u or '.jpg' in u or '.css' in u or '.js' in u or '.ico' in u:
        continue
    out.append(u)
print('after filter:', len(out))
for u in out:
    print(u[:220])
