# -*- coding: utf-8 -*-
"""从 HAR 中提取 figma_app 主 bundle / webpack-artifacts 资产 URL"""
import json, re

for path in [r'C:\Users\tndc2\Desktop\www.figma.com.har',
             r'C:\Users\tndc2\Desktop\www.figma.com2.har']:
    print('###', path)
    try:
        h = json.load(open(path, 'r', encoding='utf-8', errors='ignore'))
    except Exception as e:
        print('  ERR', e); continue
    entries = h.get('log', {}).get('entries', [])
    print('  entries:', len(entries))
    pat = re.compile(r'webpack-artifacts[^"\\]*?figma_app[^"\\]*')
    seen = set()
    for e in entries:
        u = e.get('request', {}).get('url', '')
        if 'webpack-artifacts' in u:
            m = re.search(r'assets/[^"\\?\s]+', u)
            if m and m.group(0) not in seen:
                seen.add(m.group(0))
    print('  webpack assets (%d):' % len(seen))
    for s in sorted(seen):
        print('   ', s[:130])
    # 直接找 figma_app
    fa = [u for u in (e.get('request', {}).get('url', '') for e in entries) if 'figma_app' in u]
    print('  figma_app urls:', len(fa))
    for u in fa[:10]:
        print('   ', u[:150])
    print()
