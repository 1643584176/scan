# -*- coding: utf-8 -*-
"""新旧 bundle 端点 diff: 本地 _js/app.js(旧) vs _js/prod_app.js(新)
提取各自全部 URL 字符串形态 -> 差集 = 最近新增/变更功能
"""
import re, os

here = os.path.dirname(os.path.abspath(__file__))

def extract_urls(path):
    src = open(path, encoding='utf-8', errors='replace').read()
    urls = set()
    # 字面量路径
    for m in re.finditer(r'["\'`](/(?:api|ajax-api)[^"\'`]{2,150})["\'`]', src):
        urls.add(re.split(r'[?#]', m.group(1))[0])
    # 模板拼接含 ${}
    for m in re.finditer(r'["\'`]((?:/api|/ajax-api)[^"\'`]*?\$\{[^}]{1,40}\}[^"\'`]{0,100})["\'`]', src):
        urls.add(m.group(1))
    # 独立资源段(rest 风格, 可能拼接前缀)
    for m in re.finditer(r'["\'`](/(?:projects|organizations|users|workspaces|connections|assistants|integrations|endpoints|authentication|roles|databases|operations|invites|members|branches|keys|billing|consumption|metrics|audit|subscriptions|webhooks|transfers|provisioning|agentic|genie|insights|observability|telemetry|query|sql|sessions|domains|oauth|sso|scim|mcp)[^"\'`]{1,130})["\'`]', src):
        s = m.group(1)
        if not re.match(r'^/(projects|organizations|users)$', s):
            urls.add(s)
    return urls

old = extract_urls(os.path.join(here, '_js', 'app.js'))
new = extract_urls(os.path.join(here, '_js', 'prod_app.js'))
print('old count:', len(old), 'new count:', len(new), flush=True)
print('\n=== 新增(new-only) ===', flush=True)
for s in sorted(new - old):
    print('+', s[:150], flush=True)
print('\n=== 消失(old-only) ===', flush=True)
for s in sorted(old - new):
    print('-', s[:150], flush=True)
