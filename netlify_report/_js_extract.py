# -*- coding: utf-8 -*-
"""提取 net_app.js 中 database-query 封装函数上下文"""
d = open(r'D:\scan\netlify_report\_js\net_app.js', encoding='utf-8', errors='ignore').read()
i = d.find('database-query')
print('==== 前 3500 字符 ====')
print(d[max(0, i - 3500):i])
print('==== 后 1500 字符 ====')
print(d[i:i + 1500])
