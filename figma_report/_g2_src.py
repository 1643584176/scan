# -*- coding: utf-8 -*-
# g2: 提取"请求解析链路"源码片段(toQueryParameters/addRepeated/游标/认证头)
import io, re, os
d = os.path.dirname(os.path.abspath(__file__))
JS = io.open(os.path.join(d, '_js/figma_app-main.js'), encoding='utf-8', errors='replace').read()

out = []

def grab(title, pat, before=180, after=520, limit=4):
    out.append('===== %s =====' % title)
    idxs = [m.start() for m in re.finditer(pat, JS)]
    out.append('hits: %d' % len(idxs))
    for i in idxs[:limit]:
        out.append(JS[max(0, i - before):i + after].replace('\n', ' '))
        out.append('---')

# 1 toQueryParameters 定义
grab('toQueryParameters', r'toQueryParameters', 60, 700, 4)
# 2 addRepeated
grab('addRepeated', r'addRepeated', 120, 420, 3)
# 3 request_types 枚举 + getCounts/getDashboardView
grab('request_types enum', r'ACCOUNT_TYPE_REQUEST', 100, 420, 2)
grab('getCounts', r'getCounts', 60, 420, 3)
grab('getDashboardView', r'getDashboardView', 60, 460, 3)
# 4 keyset 游标(secondary_before/secondary_column)
grab('secondary_before', r'secondary_before', 160, 420, 4)
grab('secondary_column', r'secondary_column', 140, 420, 4)
# 5 认证头
grab('X-Figma-User-ID', r'X-Figma-User-ID', 140, 300, 3)
# 6 xsrf/csrf
grab('csrf', r'csrf|XSRF|xsrf', 100, 260, 4)

io.open(os.path.join(d, '_g2_src_out.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('DONE -> _g2_src_out.txt, chars:', sum(len(x) for x in out))
