# -*- coding: utf-8 -*-
import io, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
t = open('_js/figma_app-main.js', encoding='utf-8', errors='replace').read()

# 1. fileVersionsPaginated 上下文
print('##### [fileVersionsPaginated] #####')
for m in list(re.finditer(re.escape('fileVersionsPaginated'), t))[:4]:
    a = max(0, m.start() - 500); b = min(len(t), m.end() + 400)
    print(f'--- @{m.start()} ---'); print(t[a:b]); print()

# 2. 版本历史相关 HTTP 端点:搜 url`/api 附近的 "version"
print('##### [/api/*version* URL 模板] #####')
for m in re.finditer(r'url`(/api/[^`]*version[^`]*)`', t):
    print(f'@{m.start()}: {m.group(1)}')

# 3. checkpoint 相关 API
print('##### [/api/*checkpoint* URL 模板] #####')
for m in re.finditer(r'url`(/api/[^`]*checkpoint[^`]*)`', t):
    print(f'@{m.start()}: {m.group(1)}')

# 4. 直接搜 "diff_version"
print('##### [diff_version 上下文] #####')
for m in list(re.finditer(re.escape('diff_version'), t))[:6]:
    a = max(0, m.start() - 300); b = min(len(t), m.end() + 300)
    print(f'--- @{m.start()} ---'); print(t[a:b]); print()
