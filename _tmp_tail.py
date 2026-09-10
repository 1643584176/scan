# -*- coding: utf-8 -*-
import json, io, sys, re
p = r'C:\Users\tndc2\.qoder\cache\projects\scan-72ece876\conversation-history\bf51118a\bf51118a.jsonl'
lines = open(p, encoding='utf-8', errors='replace').read().splitlines()
out = []
idx = 0
for ln in lines:
    try:
        o = json.loads(ln)
        role = o.get('role')
        if role != 'user':
            continue
        msg = o.get('message', {})
        c = msg.get('content')
        txt = ''
        if isinstance(c, list):
            for part in c:
                if isinstance(part, dict):
                    txt += (part.get('text') or '')
        else:
            txt = str(c)
        # 剥离 ide_context / system-reminder,只保留 <user_query> 内容
        m = re.search(r'<user_query>(.*?)</user_query>', txt, re.S)
        if m:
            txt = m.group(1)
        else:
            txt = re.sub(r'<ide_context>.*?</ide_context>', '[IDE]', txt, flags=re.S)
            txt = re.sub(r'<system-reminder>.*?</system-reminder>', '[SYS]', txt, flags=re.S)
        idx += 1
        out.append(f'###### USER #{idx} (len={len(txt)}) ######')
        out.append(txt[:1200])
        out.append('')
    except Exception as e:
        out.append('ERR ' + repr(e)[:120])
open(r'D:\scan\_tmp_users.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('written', len(out), 'lines; users:', idx)
