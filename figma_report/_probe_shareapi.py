# -*- coding: utf-8 -*-
"""考古: 文件分享/邀请/角色修改 的真实 API 端点 (share 弹窗 fetch 路径)"""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

data = open(r'D:\scan\figma_report\_js\figma_app-main.js', encoding='utf-8', errors='replace').read()
print('total len', len(data))

# 1. 找所有 /api/ 开头的字符串字面量, 过滤含 file/files/share/invite/user/role 的
pats = [r'"/api/[a-z0-9_/{}\-$]*"', r"'/api/[a-z0-9_/{}\-$]*'", r'`/api/[a-z0-9_/${}\-]*`']
seen = {}
for p in pats:
    for m in re.finditer(p, data):
        s = m.group(0)
        if any(k in s for k in ['share', 'invite', 'user', 'role', 'permission', 'acl', 'member']):
            seen[s] = seen.get(s, 0) + 1
for k in sorted(seen):
    print(seen[k], k)

print()
print('===== 含 {fileKey} 形态的 =====')
for m in list(re.finditer(r'[`"\']/api/[^`"\']*(?:files|file)/[^`"\']*(?:share|invite|user|role|permission|member|acl)[^`"\']*[`"\']', data))[:30]:
    print(m.group(0)[:200])
print('ALL DONE')
