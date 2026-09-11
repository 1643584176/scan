# -*- coding: utf-8 -*-
# r221pre: JS 逆向补全 —— 枚举全集 / videos 端点全集 / notification 其他调用点
import sys, io, os, re, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

js_dir = '_js'
files = glob.glob(os.path.join(js_dir, '*.js')) + glob.glob(os.path.join(js_dir, '**', '*.js'), recursive=True)
files = list(dict.fromkeys(files))
print(f'JS 文件: {len(files)} 个')

def scan(name, pattern, maxhit=25, ctx=130):
    print(f'\n### {name} —— /{pattern}/')
    hit = 0
    rx = re.compile(pattern)
    for f in files:
        try:
            txt = open(f, encoding='utf-8', errors='replace').read()
        except Exception:
            continue
        for m in rx.finditer(txt):
            s = max(0, m.start() - ctx); e = min(len(txt), m.end() + ctx)
            seg = txt[s:e].replace('\n', ' ')
            print(f'  {os.path.basename(f)}: …{seg}…')
            hit += 1
            if hit >= maxhit:
                print('  (截断)')
                return
    if hit == 0:
        print('  (无命中)')

scan('specific_admins 枚举上下文', r'specific_admins')
scan('recipient_settings 全出现', r'recipient_settings')
scan('all_admins/team_admins 候选', r'all_admins|team_admins|org_admins')
scan('videos 端点路径串', r'/videos[^"\'\s\\]{0,60}')
scan('notification_settings 全出现', r'notification_settings')
scan('frequencies 枚举候选词', r'frequency[^:]{0,40}["\'](?:daily|weekly|all|none|mentions)[^"\']{0,30}["\']')
