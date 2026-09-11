# -*- coding: utf-8 -*-
"""q25: 补充验证第二批候选（AI credits / widgets / sidebar / view 族）（本地零请求）"""
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

def show(frag, maxhits=8, ctx=100):
    print(f'\n#### {frag} ####')
    n = 0
    for name in sorted(scripts):
        if name.startswith('_q2'): continue
        txt = scripts[name]
        if frag not in txt: continue
        i = txt.find(frag)
        seg = txt[max(0, i-ctx):i+len(frag)+ctx].replace('\n', ' | ')
        print(f'  [{name}] ...{seg}...')
        n += 1
        if n >= maxhits:
            print('  (more suppressed)')
            break

show('plan_user_action_credit_usage', maxhits=5)
show('user_action_uuids', maxhits=5)
show('license_group_id', maxhits=6)
show('ai_credits/', maxhits=6)
show('usage_alert_id', maxhits=5)
show('widgets/batch', maxhits=5)
show('widgets/v2/versions', maxhits=5)
show('to_public', maxhits=5)
show('need_approval', maxhits=5)
show('favorited_resource_ids', maxhits=5)
show('user_sidebar_sentinel', maxhits=1)
show("'sidebar_section", maxhits=5)
show('hub_files/', maxhits=8)
show('saved_by_user', maxhits=5)
show('admin_recommended', maxhits=5)
show('publish_scope', maxhits=5)
