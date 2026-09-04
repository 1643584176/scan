# -*- coding: utf-8 -*-
"""INITIAL_OPTIONS 全量 key 统计 + 含 hash/url/js 的字段值"""
import re, json

c = open('D:/scan/figma_report/_js/app_file.html', 'r', encoding='utf-8', errors='ignore').read()
scripts = re.findall(r'<script(?![^>]*src)[^>]*>(.*?)</script>', c, re.S)
io_raw = scripts[3]
# 提取 JSON
m = re.search(r'\{.*\}', io_raw, re.S)
try:
    io = json.loads(m.group(0))
    print('INITIAL_OPTIONS parsed OK, top-level keys:', len(io))
    for k in sorted(io.keys()):
        v = io[k]
        vs = json.dumps(v, ensure_ascii=False)[:100] if not isinstance(v, (str, int, float, bool, type(None))) else str(v)[:100]
        print('  %-42s = %s' % (k, vs[:100]))
except Exception as e:
    print('parse err', e)
    # 正则扫描含 http 的字段
    for mm in list(re.finditer(r'"([a-z_0-9]{3,50})"\s*:\s*"(https?[^"]{0,120})"', io_raw))[:40]:
        print('  urlfield:', mm.group(1), '=', mm.group(2)[:130])
