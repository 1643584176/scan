# -*- coding: utf-8 -*-
"""提取 stringsb 输出中的路径/URL/端口线索"""
import sys, json, re

sys.stdout.reconfigure(encoding='utf-8')

path = r'F:\scan\skills\out\stringsb_strings_init_guest_20260829_131138.txt'
raw = open(path, 'rb').read().decode('utf-8', errors='replace')

# 拼接 data 字段
buf = []
for ln in raw.splitlines():
    if not ln.strip():
        continue
    try:
        j = json.loads(ln)
        if 'data' in j:
            buf.append(j['data'])
    except Exception:
        pass
text = ''.join(buf)

print('=== 路径类 ===')
paths = set()
for m in re.finditer(r'(?:GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s+(\S+)', text):
    paths.add(m.group(1))
for m in re.finditer(r'"/[A-Za-z0-9_.\-/]{2,80}"', text):
    v = m.group(0).strip('"')
    if '/' in v and not v.startswith('//'):
        paths.add(v)
for m in re.finditer(r"'/[A-Za-z0-9_.\-/]{2,80}'", text):
    v = m.group(0).strip("'")
    if '/' in v and not v.startswith('//'):
        paths.add(v)
for p in sorted(paths):
    print('PATH:', p)

print()
print('=== URL 类 ===')
urls = set()
for m in re.finditer(r'https?://[^\s"\']{4,120}', text):
    urls.add(m.group(0))
for u in sorted(urls):
    print('URL:', u)

print()
print('=== 端口/服务类 ===')
for m in re.finditer(r'[^A-Za-z](1[0-9]{4}|2[0-9]{4}|3[0-9]{4}|4[0-9]{4}|5[0-9]{4}|6[0-9]{4})[^0-9]', text):
    print('PORT?', m.group(0).strip())
