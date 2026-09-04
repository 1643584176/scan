# -*- coding: utf-8 -*-
"""找 so. 的定义: listObservabilityConfigurations: 方法定义位置 / so 的实例化"""
import re, os

here = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(here, '_js', 'app.js'), encoding='utf-8', errors='replace').read()

# 方法定义: 函数名后跟方法体
for kw in ['listObservabilityConfigurations:', 'listObservabilityConfigurations =', 
           'ObservabilityConfigurations', 'observabilityConfigurations']:
    idxs = [m.start() for m in re.finditer(re.escape(kw), src)]
    print('KW', kw, '->', len(idxs), 'occurrences', flush=True)
    for i in idxs[:5]:
        print('---', flush=True)
        print(src[max(0, i - 900):i + 200].replace('\n', ' ')[:1100], flush=True)
