# -*- coding: utf-8 -*-
"""从 338MB HAR 提取 webpack JS 资产并解压 brotli,供静态分析"""
import json, os, base64

HAR = 'C:/Users/tndc2/Desktop/www.figma.com.har'
OUTDIR = 'D:/scan/figma_report/_js/'
os.makedirs(OUTDIR, exist_ok=True)

with open(HAR, 'r', encoding='utf-8') as f:
    har = json.load(f)

saved = 0
for e in har['log']['entries']:
    url = e['request']['url']
    if '/webpack-artifacts/' not in url:
        continue
    resp = e['response']
    content = resp.get('content', {})
    text = content.get('text')
    if not text:
        continue
    # 文件名
    name = url.split('/')[-1]
    if name.endswith('.br'):
        # brotli 压缩 -> 原始字节
        try:
            raw = base64.b64decode(text)
        except Exception:
            continue
        path = os.path.join(OUTDIR, name)
        with open(path, 'wb') as f:
            f.write(raw)
        saved += 1
print('saved br files:', saved)
# 大小统计
tot = 0
for fn in os.listdir(OUTDIR):
    sz = os.path.getsize(os.path.join(OUTDIR, fn))
    tot += sz
    if sz > 500000:
        print('  %-70s %d' % (fn, sz))
print('total bytes:', tot)
