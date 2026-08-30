# -*- coding: utf-8 -*-
"""从历史 transcript 提取 23456/30001/30002 相关上下文"""
import json, sys

path = r'C:\Users\lbb.LAPTOP-LU4P5L6T\.qoder\cache\projects\scan-dcb95ef8\conversation-history\04936518\04936518.jsonl'
kw = ['23456', '30001', '30002', 'connectrpc', 'connect-rpc', '方法矩阵', 'exp_k4']
out = []
with open(path, encoding='utf-8') as f:
    for i, ln in enumerate(f):
        if not any(k in ln for k in kw):
            continue
        try:
            d = json.loads(ln)
            texts = [c.get('text', '') for c in d['message']['content'] if c.get('type') == 'text']
            for t in texts:
                if any(k in t for k in kw):
                    out.append('LINE %d ROLE %s' % (i, d['role']))
                    out.append(t[:1200])
                    out.append('---')
        except Exception as e:
            out.append('err %d %s' % (i, e))

sys.stdout.reconfigure(encoding='utf-8')
print('\n'.join(out[:80]))
