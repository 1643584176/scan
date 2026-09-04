# -*- coding: utf-8 -*-
"""app.js: provisioned-instances 页面路由定义 -> 确定资源层级(project/org)
搜路由注册表(路径字符串 + 组件引用) 与 sidebar 菜单链接
"""
import re, os

here = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(here, '_js', 'prod_app.js'), encoding='utf-8', errors='replace').read()
out = []

# 1. 路由路径字面量含 provisioned / lakebase 的
for m in re.finditer(r'["\'`]([^"\'`]*provisioned[^"\'`]*)["\'`]', src):
    out.append('ROUTE-LIT: ' + m.group(1)[:200])
for m in re.finditer(r'["\'`]([^"\'`]*lakebase[^"\'`]*)["\'`]', src):
    s = m.group(1)
    if any(x in s for x in ['/', '-', ':']):
        out.append('LAKEBASE-LIT: ' + s[:200])

# 2. ProvisionedInstancesList chunk 引用处(懒加载映射里页面 URL 与 chunk 的关联)
for m in re.finditer(r'ProvisionedInstances\w*', src):
    i = m.start()
    seg = src[max(0, i - 200):i + 300].replace('\n', ' ')
    out.append('CHUNKREF: ' + seg[:450])

# 3. 找 loadable 路由表: 类似 {path:"/projects/:id/...",component:()=>import(...)} 的结构
# 常见 minify 形态: path:"..." 后跟 element/Component
for m in re.finditer(r'path:"(/[^"]{3,90})"', src):
    p = m.group(1)
    if any(k in p for k in ['instance', 'project', 'org', 'database', 'setting']):
        out.append('PATH: ' + p)

open(os.path.join(here, '_p54_out.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('done lines:', len(out), flush=True)
