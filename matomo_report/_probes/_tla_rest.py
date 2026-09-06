# -*- coding: utf-8 -*-
import re

root = r'F:\scan\matomo_report\_src\matomo'
targets = {
    'getSelectQueryWhereNameContains': r'core\Tracker\TableLogAction.php',
    'getIdActionMatchingNameAndType': None,  # search all
}

src_tla = open(root + r'\core\Tracker\TableLogAction.php', encoding='utf-8', errors='replace').read()
idx = src_tla.find('function getSelectQueryWhereNameContains')
if idx != -1:
    rest = src_tla[idx:]
    nxt = re.search(r'\n    (public|protected|private) function ', rest[10:])
    end = idx + 10 + (nxt.start() if nxt else len(rest))
    print('== getSelectQueryWhereNameContains ==')
    print(src_tla[idx:end][:1500])

# find Model class used by TableLogAction::getModel
m = re.search(r'function getModel\(\).*?return (.*?);', src_tla, re.S)
print()
print('getModel:', m.group(1).strip() if m else 'n/a')

# search getIdActionMatchingNameAndType across core/plugins
import os
for base in ('core', 'plugins'):
    for dp, dns, fns in os.walk(os.path.join(root, base)):
        dns[:] = [d for d in dns if d not in {'.git', 'node_modules', 'tests', 'vendor', 'Updates'}]
        for fn in fns:
            if not fn.endswith('.php'):
                continue
            p = os.path.join(dp, fn)
            s = open(p, encoding='utf-8', errors='replace').read()
            i = s.find('function getIdActionMatchingNameAndType')
            if i != -1:
                rest = s[i:]
                nxt = re.search(r'\n    (public|protected|private) function ', rest[10:])
                end = i + 10 + (nxt.start() if nxt else len(rest))
                print()
                print('== %s:%d ==' % (os.path.relpath(p, root), s.count('\n', 0, i) + 1))
                print(s[i:end][:1800])
