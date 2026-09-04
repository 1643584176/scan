# -*- coding: utf-8 -*-
"""index-LpJ7SKi1.js 完整性验证 + bat 类方法分布:
搜 np 调用的方法名是否在文件中定义(判断下载完整/方法是否在 bat)
"""
import re, os

here = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(here, '_js', 'prod_chunks', 'index-LpJ7SKi1.js')
src = open(p, encoding='utf-8', errors='replace').read()
out = []
out.append('file size: %d' % len(src))

for kw in ['getCustomerManagedKey', 'getCustomerManagedKeyStatus', 'runProjectSqlQuery',
           'getWorkspaceNetworkStatus', 'generateDatabaseCredential', 'generateOAuthToken',
           'listDatabaseInstances', 'getResolveRegions']:
    idxs = [m.start() for m in re.finditer(re.escape(kw), src)]
    out.append('KW %s -> %d' % (kw, len(idxs)))
    for i in idxs[:3]:
        out.append('  @%d: %s' % (i, src[max(0, i - 150):i + 200].replace('\n', ' ')[:330]))

# bat 类范围: class bat 到下一个 class
i_bat = src.find('class bat extends yat')
out.append('bat class start: %d' % i_bat)
# 找 bat 类结尾: 找 "const Kde" (Le 实例化前面)
i_kde = src.find('const Kde')
out.append('Kde/Le 位置: %d (距 bat start %d)' % (i_kde, i_kde - i_bat))

# bat 类内方法数量: 数 箭头函数字段 形态 xxx=( 数量
if i_bat >= 0 and i_kde > i_bat:
    seg = src[i_bat:i_kde]
    methods = re.findall(r'([A-Za-z_$][\w$]*)=\(', seg)
    out.append('bat class methods count: %d' % len(methods))
    # 打印所有方法名看是否有 lakebase 相关
    lb = [m2 for m2 in methods if any(k in m2.lower() for k in ['instance', 'lake', 'catalog', 'role', 'permission', 'observ', 'resolve', 'credential', 'oauth', 'workspace', 'sql'])]
    out.append('interesting methods: %s' % ', '.join(lb[:60]))

open(os.path.join(here, '_p76_out.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('done lines:', len(out), flush=True)
