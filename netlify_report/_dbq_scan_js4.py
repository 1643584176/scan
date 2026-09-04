# -*- coding: utf-8 -*-
"""扫 net_app.js:database branch 相关 API 路径(GraphQL or REST)"""
import re

data = open(r'D:\scan\netlify_report\_js\net_app.js', encoding='utf-8', errors='ignore').read()

# 1. 删除分支 mutation 附近找路径
print('== Failed to delete the branch 上下文 ==')
i = data.find('Failed to delete the branch')
print(data[max(0, i - 1500):i + 200].replace('\n', ' '))
print()

# 2. database branch 创建相关操作
print('== 关键词:database branch 创建/列表 ==')
for kw in ['createDatabase', 'databaseBranch', 'DatabaseBranch', 'create_branch', 'new-branch', 'database/branches',
           'database/branch', 'branches?', 'production-branch', 'database_production']:
    for m in list(re.finditer(re.escape(kw), data))[:2]:
        i = m.start()
        print('-- %s --' % kw)
        print('  ...%s...' % data[max(0, i - 250):i + 250].replace('\n', ' '))
        print()
