# -*- coding: utf-8 -*-
"""解码 supabase_report 各脚本中硬编码 JWT 的 role,判断 anon 还是 service。"""
import base64, io, json, os, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
root = r'D:\scan\supabase_report'
jwt_rx = re.compile(r'eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{8,}')
for fn in sorted(os.listdir(root)):
    if not fn.endswith('.py'):
        continue
    fp = os.path.join(root, fn)
    try:
        txt = open(fp, 'r', encoding='utf-8', errors='replace').read()
    except Exception:
        continue
    for m in jwt_rx.findall(txt):
        try:
            payload = m.split('.')[1] + '=' * (-len(m.split('.')[1]) % 4)
            data = json.loads(base64.urlsafe_b64decode(payload))
            role = data.get('role', '?')
            exp = data.get('exp', '?')
            ref = data.get('ref', '?')
            print(fn, '| role=%s | exp=%s | ref=%s' % (role, exp, ref))
        except Exception as e:
            print(fn, '| decode-fail', str(e)[:60])
        break  # 每文件只看第一个
