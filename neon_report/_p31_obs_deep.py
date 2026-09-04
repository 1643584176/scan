# -*- coding: utf-8 -*-
"""observability 功能面完整挖掘:
1. listObservabilityConfigurations / listObservabilityConfigurations 定义
2. 'ajax-api' 全部出现位置与端点
3. richUser GraphQL 查询上下文(可能其他查询)
4. so.instance / so. 的 client 定义与 baseURL
"""
import re, os

here = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(here, '_js', 'app.js'), encoding='utf-8', errors='replace').read()

def show(kw, maxn=4, before=500, after=700):
    print('=' * 70, flush=True)
    print('KEY:', kw, flush=True)
    idxs = [m.start() for m in re.finditer(re.escape(kw), src)]
    print('occurrences:', len(idxs), flush=True)
    for i in idxs[:maxn]:
        print('--- ctx %d ---' % i, flush=True)
        print(src[max(0, i - before):i + after].replace('\n', ' ')[:1600], flush=True)

show('listObservabilityConfigurations', 3)
show('ObservabilityConfigurations', 3)
show('ajax-api', 5, 300, 300)
show('richUser', 3, 400, 400)
show('insights_agent_config', 2, 300, 500)
