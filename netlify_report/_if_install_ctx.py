# -*- coding: utf-8 -*-
"""bundle:install-extension / fetch-extension / extension-proxy 的调用 body 结构"""
import re

data = open(r'D:\scan\netlify_report\_js\net_app.js', encoding='utf-8', errors='ignore').read()

for kw in ['functions/install-extension', 'functions/fetch-extension', 'functions/extension-proxy',
           'functions/manage-extension-proxy']:
    hits = [m.start() for m in re.finditer(re.escape(kw), data)]
    print('== %s (%d) ==' % (kw, len(hits)))
    for i in hits[:4]:
        print('  ...%s...' % data[max(0, i - 900):i + 900].replace('\n', ' '))
        print()
