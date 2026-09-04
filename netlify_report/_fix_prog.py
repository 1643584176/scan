# -*- coding: utf-8 -*-
"""清理 progress 中被截断的重复段落"""
p = r'D:\scan\netlify_report\progress-2026-09-02.md'
s = open(p, encoding='utf-8').read()
cut = '### PATCH /api/v1/sites/{id} 字段级攻击 —— 关闭(mass assignment 面打穿)\n'
i = s.find(cut)
if i != -1:
    # 第一个(截断的)版本从出现处到第二个版本前删除
    j = s.find(cut, i + 1)
    if j != -1:
        s = s[:i] + s[j:]
        open(p, 'w', encoding='utf-8').write(s)
        print('removed truncated dup, len', len(s))
    else:
        print('only one occurrence, nothing to fix')
else:
    print('marker not found')
