# -*- coding: utf-8 -*-
import os, time
d = os.path.dirname(os.path.abspath(__file__))
items = []
for f in os.listdir(d):
    if f.endswith('.md') or f.endswith('.json') and not f.startswith('_r'):
        p = os.path.join(d, f)
        items.append((os.path.getmtime(p), f, os.path.getsize(p)))
items.sort(reverse=True)
for mt, f, sz in items:
    print(time.strftime('%m-%d %H:%M', time.localtime(mt)), f, sz)
