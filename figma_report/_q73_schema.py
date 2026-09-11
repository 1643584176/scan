# -*- coding: utf-8 -*-
# q73: 挖 PaginatedFilesSchemaValidator 完整定义 + 调用点完整参数对象 + toAPIParameters
import sys, io, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

F = r'D:\scan\figma_report\_js\935-431f89677a39072c.min.js'
t = open(F, encoding='utf-8', errors='replace').read()
print(f'文件长度: {len(t)}')

# 1) paginated_files 调用点完整上下文（前 3000 字符）
i = t.find('paginated_files')
print('\n===== 1) 调用点前 3000 字符 =====')
print(t[max(0, i - 3000):i + 200])

# 2) PaginatedFilesSchemaValidator 定义搜索
print('\n===== 2) PaginatedFilesSchemaValidator 全部出现 =====')
for m in re.finditer(r'PaginatedFilesSchemaValidator', t):
    st = max(0, m.start() - 100)
    print(f'--- @{m.start()} ---')
    print(' ', t[st:m.end() + 400].replace('\n', ' ')[:600])

# 3) toAPIParameters 定义
print('\n===== 3) toAPIParameters 定义 =====')
for m in list(re.finditer(r'toAPIParameters', t))[:6]:
    st = max(0, m.start() - 150)
    print(f'--- @{m.start()} ---')
    print(' ', t[st:m.end() + 350].replace('\n', ' ')[:500])
print('DONE q73')
