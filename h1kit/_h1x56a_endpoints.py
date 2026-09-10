# -*- coding: utf-8 -*-
"""h1x56a: bundle 全量端点提取 - fetch/相对URL 对比已测面找遗漏"""
import io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
data = open(r'D:\scan\h1kit\_h1x4_app.js', encoding='utf-8', errors='replace').read()

# 1) fetch(`...`) / fetch("...") 字面量
f1 = re.findall(r'fetch\([`"]([^`"]{1,200})[`"]', data)
# 2) 常见请求封装:axios.get/post/put/delete(`...`),  XHR open("GET","...")
f2 = re.findall(r'(?:get|post|put|delete|patch|request)\([`"]([^`"]{1,200})[`"]', data)
# 3) 含模板的 URL 字符串(相对路径,排除 assets/graphql/静态)
allu = set(f1) | set(f2)
rel = []
for u in allu:
    u2 = u.strip()
    if not u2.startswith('/'):
        continue
    if u2.startswith(('/assets', '/graphql', '/static')):
        continue
    # 去 query
    p = u2.split('?')[0]
    rel.append((u2, p))

print('fetch literal count:', len(allu))
print('relative endpoints:', len(rel))
seen = {}
for full, p in rel:
    seen.setdefault(p, []).append(full)

# 4) 过滤已测面关键词(直接排除)
KNOWN = ['/reports/', '/bugs', '/inbox', '/notifications', '/hacktivity', '/programs', '/users',
         '/hai/', '/attachments', '/export', '/search', '/opportunities', '/teams', '/organizations',
         '/subjects', '/sitemap', '/robots', '/graphql', '/api/', '/policies', '/vdp', '/pentest',
         '/invitations', '/collaborators', '/summaries', '/mediations', '/weaknesses', '/cve', '/researcher',
         '/hackers', '/security', '/swag', '/settings', '/earnings', '/payments', '/tax', '/bounty',
         '/challenges', '/directory', '/leaderboard', '/resources', '/support', '/help', '/docs',
         '/webhooks', '/triggers', '/automations', '/integrations', '/jira', '/linear', '/slack',
         '/credentials', '/scopes', '/assets']

print()
print('=== candidate unknown endpoints (not matching known prefix) ===')
cand = []
for p in sorted(seen.keys()):
    if any(p.startswith(k) for k in KNOWN):
        continue
    cand.append(p)
for p in cand:
    print(p[:160], '| e.g.', seen[p][0][:200])
print()
print('total candidates:', len(cand))
