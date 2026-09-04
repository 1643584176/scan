# -*- coding: utf-8 -*-
"""分析 zip-it-and-ship-it 注入的 telemetry 模块:找内部端点 / token 用法 / 网络目标"""
import re, sys
sys.path.insert(0, r'D:\scan\netlify_report')
import zipfile

z = zipfile.ZipFile(r'D:\scan\netlify_report\_zisi\out2\probe1.zip')
data = z.read('___netlify-telemetry.mjs').decode('utf-8', 'replace')
print('size:', len(data))
# 找 URL / host
urls = sorted(set(re.findall(r'https?://[A-Za-z0-9._\-/:]+', data)))
print('--- urls ---')
for u in urls[:50]:
    print(u)
hosts = sorted(set(re.findall(r'["\']([A-Za-z0-9.\-]+\.[a-z]{2,}["\']?)', data)))
# 找域名
doms = sorted(set(re.findall(r'[A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)+\.[a-z]{2,}', data)))
print('--- domains ---')
for d in doms[:60]:
    print(d)
# 找 token/env 引用
for kw in ['NETLIFY_FUNCTIONS_TOKEN', 'FUNCTIONS_TOKEN', 'AWS_LAMBDA_METADATA_TOKEN', 'metadata', 'token', 'bearer', 'Authorization']:
    idxs = [m.start() for m in re.finditer(kw, data)][:5]
    print('--- %s @ %s ---' % (kw, idxs))
    for i in idxs:
        print(data[max(0, i - 120):i + 200].replace('\n', ' ')[:320])
