# -*- coding: utf-8 -*-
import re
for fn in [r'D:\scan\netlify_report\_js\net_app.js', r'D:\scan\netlify_report\_js\net_actions.js', r'D:\scan\netlify_report\_js\net_lib.js']:
    try:
        t = open(fn, encoding='utf-8', errors='ignore').read()
    except Exception as e:
        continue
    print('########', fn.split('\\')[-1], 'len', len(t))
    for name in ['identeer-proxy', 'git', 'verify', 'hubspot']:
        hits = [m.start() for m in re.finditer(re.escape('/' + name), t)]
        hits += [m.start() for m in re.finditer(re.escape(name + '?'), t)]
        hits += [m.start() for m in re.finditer(re.escape(name + '"'), t)]
        if not hits:
            print('---', name, 'no hits')
            continue
        print('---', name, 'hits:', len(set(hits)))
        shown = 0
        for h in sorted(set(hits)):
            s = max(0, h - 120)
            print(t[s:h + 260].replace('\n', ' ')[:360])
            print('.')
            shown += 1
            if shown >= 2:
                break
