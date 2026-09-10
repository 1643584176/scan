# -*- coding: utf-8 -*-
"""h1x55a: bundle 扫描 - image/proxy/upload/pdf/print/preview/screenshot/render 端点"""
import re, io, sys, glob, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

files = [r'D:\scan\h1kit\_h1x4_app.js', r'D:\scan\h1kit\_h1x4_vendor.js']
pat = re.compile(r'["\'`](/(?:assets|attachments|images?|uploads?|proxy|preview|thumbnails?|screenshots?|print|pdf|render|export|download|files?|media|static|blobs?|files|document|reports?/[A-Za-z0-9_\-{}.$]+/(?:print|pdf|screenshots?|attachments?|export|preview|render|activities?|versions?))[A-Za-z0-9_\-/{}?&=.$%:#]*)["\'`]', re.I)
img_pat = re.compile(r'["\'`]([^"\'`]*(?:image|img|proxy|upload|preview|thumbnail|screenshot|attachment|blob|signed)[^"\'`]*)["\'`]', re.I)

for f in files:
    if not os.path.exists(f):
        print('MISS', f); continue
    data = open(f, encoding='utf-8', errors='replace').read()
    print('###', os.path.basename(f), len(data))
    seen = set()
    for m in pat.finditer(data):
        s = m.group(1)
        if s not in seen:
            seen.add(s)
            print(' URL:', s[:200])
    # 上下文提取:含 render/proxy 语义的调用片段
    for kw in ['image_proxy', 'img_proxy', 'proxyUrl', 'proxy_url', 'renderMarkdown', 'markdown', 'previewUrl', 'downloadUrl', 'expiring_url', 'screenshotUrl', 'attachmentUrl']:
        idx = 0
        cnt = 0
        while cnt < 6:
            i = data.find(kw, idx)
            if i < 0: break
            ctx = data[max(0, i - 150):i + 200]
            # 只留可读片段(去超长)
            if ctx not in seen:
                seen.add(ctx)
                print(' CTX[%s]: ...%s...' % (kw, ctx.replace('\n', ' ')[:330]))
            idx = i + len(kw)
            cnt += 1
