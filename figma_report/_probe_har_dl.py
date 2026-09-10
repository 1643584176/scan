# -*- coding: utf-8 -*-
"""从原始 HAR 找 .fig 下载/导出/save 类真实请求 (A 账号操作)"""
import sys, io, re, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HAR = 'C:/Users/tndc2/Desktop/www.figma.com.har'
print('loading HAR...')
with open(HAR, 'r', encoding='utf-8') as f:
    har = json.load(f)
entries = har['log']['entries']
print('entries:', len(entries))

kws = ['canvas', 'download', 'export', 'save_local', 'local_copy', '/fig', 'copy_to', 'save_copy',
       'fig-download', 'file_download']
n = 0
for e in entries:
    url = e['request']['url']
    lu = url.lower()
    if any(k in lu for k in kws) and len(lu) < 260:
        st = e['response']['status']
        ct = e['response']['content'].get('mimeType', '')
        size = e['response'].get('_transferSize', e['response']['content'].get('size', 0))
        print(f'{e["request"]["method"]:6s} {st} {ct[:35]:35s} {size:>10d}  {url}')
        n += 1
        if n > 120:
            break
print('shown', n)
print('ALL DONE')
