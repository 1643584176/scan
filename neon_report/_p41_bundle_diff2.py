# -*- coding: utf-8 -*-
"""新旧 bundle 全路径字面量 diff(放宽)"""
import re, os

here = os.path.dirname(os.path.abspath(__file__))

def extract(path):
    src = open(path, encoding='utf-8', errors='replace').read()
    urls = set()
    # 所有 /xxx/yyy 形态字面量(长度>=4, 不含空格/引号/特殊字符)
    for m in re.finditer(r'["\'`](/[A-Za-z0-9_.${}/-]{3,130})["\'`]', src):
        urls.add(m.group(1))
    return urls

old = extract(os.path.join(here, '_js', 'app.js'))
new = extract(os.path.join(here, '_js', 'prod_app.js'))
print('old:', len(old), 'new:', len(new), flush=True)

only_new = sorted(new - old)
only_old = sorted(old - new)
# 过滤常见噪音(/、/assets 等)
def noise(s):
    return (s.count('/') < 2 or len(s) < 6 or
            any(x in s for x in ['assets', '.png', '.svg', '.ico', '.css', '.woff', 'fonts', '/_next/', 'cloudfront']))
fn = [s for s in only_new if not noise(s)]
fo = [s for s in only_old if not noise(s)]
print('\n=== 新增路径(%d) ===' % len(fn), flush=True)
for s in fn[:80]:
    print('+', s[:130], flush=True)
print('\n=== 消失路径(%d) ===' % len(fo), flush=True)
for s in fo[:60]:
    print('-', s[:130], flush=True)
