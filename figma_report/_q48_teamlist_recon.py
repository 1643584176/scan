# -*- coding: utf-8 -*-
# q48: 找「列 team」端点 + users/me 调用（数据面横向的最后一查）
import sys, io, os, re, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

files = list(dict.fromkeys(glob.glob('_js/**/*.js', recursive=True) + glob.glob('_js/*.js')))
print(f'JS 文件: {len(files)} 个')

def scan(name, pattern, maxhit=14, ctx=150):
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
            print(f'  {os.path.basename(f)}: …{txt[s:e].replace(chr(10), " ")}…')
            hit += 1
            if hit >= maxhit:
                print('  (截断)'); return
    if hit == 0:
        print('  (无命中)')

scan('getTeams/teams 列表调用', r'getTeams|teams\b[^/]{0,25}get\(t\.url', maxhit=12)
scan('/api/teams 路径串', r'/api/teams[^"\'`\s\\]{0,50}', maxhit=12)
scan('users/me 调用', r'/api/users/[^"\'`\s\\]{0,40}', maxhit=12)
scan('getMe/currentUser 调用', r'getMe\b|current_user|/api/me\b', maxhit=10)
scan('team 列表 GraphQL/内部 API', r'team_list|teams_for_user|userTeams|getUserTeams', maxhit=10)
