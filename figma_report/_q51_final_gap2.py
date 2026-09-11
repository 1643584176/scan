# -*- coding: utf-8 -*-
# q51: 四连问最终盘点 —— 核查「方法覆盖/身份参数/条件请求/bell/user-state/新语法」是否已打
import sys, io, os, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

files = sorted(glob.glob('_figma_r2*.py') + glob.glob('_q4*.py') + glob.glob('_q5*.py') + glob.glob('*.py'))
files = [f for f in files if f.startswith(('_figma_r2', '_q4', '_q5', '_et'))][:2000]
print(f'脚本池: {len(files)} 个\n')

checks = [
    ('方法覆盖头', r'Method-Override|X-HTTP-Method|method_override'),
    ('身份/扮演参数', r'user_id=|actor_id|impersonat|as_user|acting_user'),
    ('条件请求头', r'If-None-Match|If-Modified-Since|if_none_match'),
    ('bell 端点', r'user_notifications_bell'),
    ('user/state 端点', r'user/state|fuid'),
    ('井号 %23', r'%23|\\x23'),
    ('科学计数', r'e\+?\d|e18|E18'),
    ('双负号', r'--1666|--1'),
    ('零宽字符', r'200b|200B|feff|FEFF|u200b'),
    ('真实 UID 作 recipient', r'recipients.*:\s*\[UID_A\]|\[UID_A\]'),
    ('PUT ntype 自由值', r"ntype.*junk|notification_type.*junk.*PUT|junk.*ntype"),
    ('recipients 真值族', r'recipients.*UID_A|UID_A.*recipients'),
]
for name, pat in checks:
    hits = []
    rx = None
    try:
        rx = __import__('re').compile(pat)
    except Exception as e:
        print(f'## {name}: 正则错误 {e}'); continue
    for f in files:
        try:
            txt = open(f, encoding='utf-8', errors='replace').read()
        except Exception:
            continue
        if rx.search(txt):
            hits.append(f)
    tag = '已打' if hits else '★未打'
    print(f'## [{tag}] {name}  ({len(hits)} 脚本)')
    for h in hits[:6]:
        print(f'    {h}')
