# -*- coding: utf-8 -*-
"""q24: 定向验证 —— 对 q23 暴露的疑似盲区，打印命中上下文以判定"真盲区 vs 已覆盖"（本地零请求）"""
import sys, io, re, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DIR = r'D:\scan\figma_report'
scripts = {}
for f in os.listdir(DIR):
    if f.endswith('.py') and (f.startswith('_figma_') or f.startswith('_tmp_') or f.startswith('_q') or f.startswith('_et')):
        try: scripts[f] = open(os.path.join(DIR, f), encoding='utf-8', errors='ignore').read()
        except Exception: pass
    elif f.endswith('.txt') and (f.startswith('_r') or f.startswith('_w') or f.startswith('_q')):
        try: scripts[f] = open(os.path.join(DIR, f), encoding='utf-8', errors='ignore').read()
        except Exception: pass

def show(frag, maxhits=6, ctx=90, name_filter=None):
    print(f'\n#### {frag} ####')
    n = 0
    for name in sorted(scripts):
        if name.startswith('_q2'): continue   # 排除本侦查系列
        txt = scripts[name]
        if frag not in txt: continue
        if name_filter and not name_filter(name): continue
        # 找所有出现位置, 打印首个上下文
        i = txt.find(frag)
        seg = txt[max(0, i-ctx):i+len(frag)+ctx].replace('\n', ' | ')
        print(f'  [{name}] ...{seg}...')
        n += 1
        if n >= maxhits: 
            print('  (more suppressed)')
            break

# 1) group_by_team 实际请求？
show('group_by_team')
# 2) multiplayer copy 面（v54 hubops 是 JS 逆向; 看有无实际请求）
show('multiplayer/')
show("'/copy'")
show('/copy', name_filter=lambda n: n.startswith('_figma_r') or n.startswith('_figma_v'))
# 3) /api/resources 本体请求（仅脚本, 排除 q 侦查）
show("'/api/resources'", name_filter=lambda n: n.endswith('.py'))
show('"api/resources"', maxhits=4)
show("/api/resources',", maxhits=4)
# 4) files/batch
show('/api/files/batch', maxhits=4)
show('files_batch', maxhits=4)
# 5) widgets/v2/versions
show('widgets/v2', maxhits=4)
show('widget_ids', maxhits=4)
# 6) spell-check-words 测试
show('spell-check', maxhits=4)
# 7) teams/create / org_invites / planless
show('teams/create', maxhits=4)
show('org_invites', maxhits=4)
show('planless', maxhits=4)
# 8) 已打面深尾参数
show('tags=', maxhits=5)
show('workspace_filter', maxhits=4)
show('recent_prototypes', maxhits=4)
show('thumbnail_guid', maxhits=5, name_filter=lambda n: n.endswith('.py'))
show('open_file_key', maxhits=4)
