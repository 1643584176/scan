# -*- coding: utf-8 -*-
import json, os, re
base = r'D:\scan\netlify_report'
for f in ['_aws_creds.json', '_aws_creds1.json', '_aws_creds2.json']:
    p = os.path.join(base, f)
    if not os.path.exists(p):
        print(f, 'missing')
        continue
    d = json.load(open(p, encoding='utf-8'))
    print(f, '-> account:', d.get('account'), '| keys:', list(d.keys()))
    # 掩码 token
    st = d.get('session_token') or ''
    print('   session_token len:', len(st), 'head:', st[:24] if st else '')
# probe4 输出完整性
p4 = os.path.join(base, '_probe4_out.json')
if os.path.exists(p4):
    raw = open(p4, encoding='utf-8', errors='replace').read()
    print()
    print('_probe4_out.json size:', len(raw))
    # 找 extension 凭据之外的字段
    for key in ['extEnv', 'proc2', 'proc1', 'net', 'cred', 'aws', 'token']:
        for m in re.finditer(key, raw):
            s = max(0, m.start() - 60)
            print('...', raw[s:m.start() + 160].replace('\n', ' ')[:220])
            break
