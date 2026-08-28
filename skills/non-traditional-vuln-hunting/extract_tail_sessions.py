# -*- coding: utf-8 -*-
"""梳理 494b74ea + a669521c 会话: 最后的实验与放弃原因"""
import json, re, sys

def extract(fp, out_fp, start_hit=None):
    out = []
    with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if obj.get('role') != 'assistant':
                continue
            msg = obj.get('message', {})
            content = msg.get('content')
            if not isinstance(content, list):
                continue
            for item in content:
                if not isinstance(item, dict) or item.get('type') != 'text':
                    continue
                t = item.get('text', '')
                t = t.replace('\n', ' ')
                if len(t) < 30:
                    continue
                out.append(t)
    with open(out_fp, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out))
    return len(out)

for sid, fp, ofp in [
    ('494b74ea', r'C:\Users\tndc2\.qoder\cache\projects\scan-72ece876\conversation-history\494b74ea\494b74ea.jsonl',
     r'D:\scan\skills\non-traditional-vuln-hunting\494b74ea_text.txt'),
    ('a669521c', r'C:\Users\tndc2\.qoder\cache\projects\scan-72ece876\conversation-history\a669521c\a669521c.jsonl',
     r'D:\scan\skills\non-traditional-vuln-hunting\a669521c_text.txt'),
]:
    n = extract(fp, ofp)
    print(sid, 'segments:', n)
