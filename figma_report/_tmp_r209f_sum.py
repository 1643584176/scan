# -*- coding: utf-8 -*-
# r209f: 汇总 _r209e_*.txt 结果（状态码/耗时/关键字段）
import io, os, re, glob
d = os.path.dirname(os.path.abspath(__file__))

rows = []
for f in sorted(glob.glob(os.path.join(d, '_r209e_*.txt'))):
    name = os.path.basename(f).replace('_r209e_', '').replace('.txt', '')
    txt = io.open(f, encoding='utf-8', errors='replace').read()
    m = re.match(r'HTTP (\d+) (\d+)ms (.+)', txt)
    sc, dt = (m.group(1), m.group(2)) if m else ('?', '?')
    # URL 中的查询值
    url = m.group(3) if m else ''
    qv = re.search(r'mentioned_user_id=([^&]+)', url)
    qv = qv.group(1) if qv else ''
    body = txt.split('}\n', 1)[-1] if '}\n' in txt else txt
    body = txt[txt.find('\n\n')+2:] if '\n\n' in txt else txt
    # 提取关键 JSON 片段
    meta = ''
    mm = re.search(r'"meta":\s*(\{.*?\})', body, re.S)
    if mm:
        meta = mm.group(1)[:160]
    else:
        msg = re.search(r'"message":\s*"([^"]*)"', body)
        if msg:
            meta = '"message": "' + msg.group(1) + '"'
        elif '<!DOCTYPE' in body:
            meta = '[SPA HTML %d bytes]' % len(body)
    rows.append('%s | %s %sms | %s | %s' % (name, sc, dt, qv[:40], meta.replace('\n', ' ')[:170]))

io.open(os.path.join(d, '_r209f_summary.txt'), 'w', encoding='utf-8').write('\n'.join(rows))
print('\n'.join(rows))
