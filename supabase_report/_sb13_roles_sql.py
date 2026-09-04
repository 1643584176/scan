# -*- coding: utf-8 -*-
"""公开侦察13: SQL 编辑器角色列表 SQL 完整提取 (es 定义/rolname 上下文)"""
import re, os, glob

here = os.path.dirname(os.path.abspath(__file__))
jsdir = os.path.join(here, '_sb_js')
out = []

def dump(fp, key_regexes, ctx=900, maxhit=6):
    name = os.path.basename(fp)
    src = open(fp, encoding='utf-8', errors='replace').read()
    hit = 0
    for m in re.finditer(key_regexes, src):
        i = m.start()
        seg = src[max(0, i - ctx):i + ctx].replace('\n', ' ')
        out.append('### %s @%d: %s' % (name, i, seg[:1700]))
        hit += 1
        if hit >= maxhit:
            break
    return hit

# 1. 主 client 中 roles SQL (es 定义、with roles as)
for fp in glob.glob(os.path.join(jsdir, '099kov3mfam-s.js')):
    src = open(fp, encoding='utf-8', errors='replace').read()
    # 找 with roles as 的完整定义 (通常 1-3KB)
    for m in re.finditer(r'roles\s+as\s*\(', src):
        i = m.start()
        seg = src[max(0, i - 1500):i + 2500].replace('\n', ' ')
        out.append('### roles-cte @%d: %s' % (i, seg[:3900]))
        break
    # rolname / pg_roles 出现处 (角色枚举 SQL 核心)
    for m in re.finditer(r'rolname|pg_roles|pg_roles_visible|has_role', src):
        i = m.start()
        seg = src[max(0, i - 500):i + 500].replace('\n', ' ')
        out.append('### rol-ref @%d: %s' % (i, seg[:950]))
        if len(out) > 60:
            break

# 2. 0h9x8dhtehorj.js (SQL 编辑器 chunk) 中角色相关
fp2 = os.path.join(jsdir, '0h9x8dhtehorj.js')
if os.path.exists(fp2):
    src2 = open(fp2, encoding='utf-8', errors='replace').read()
    for m in re.finditer(r'rolname|pg_roles|role.*list|listRoles|includeDefaultRoles', src2):
        i = m.start()
        seg = src2[max(0, i - 600):i + 600].replace('\n', ' ')
        out.append('### edit-chunk @%d: %s' % (i, seg[:1150]))

open(os.path.join(here, '_sb13_roles.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('lines:', len(out), flush=True)
