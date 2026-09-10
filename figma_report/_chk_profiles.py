# -*- coding: utf-8 -*-
"""检查 p99/p101 保存 JSON 的 profile/author 字段结构 — 找敏感泄露"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def walk(o, path='', depth=0):
    """遍历 JSON 找 author/profile/publisher/email 相关字段"""
    hits = []
    if depth > 6:
        return hits
    if isinstance(o, dict):
        for k, v in o.items():
            kl = k.lower()
            if any(s in kl for s in ['email', 'phone', 'ip', 'token', 'secret', 'private', 'internal']):
                hits.append((path + '.' + k, str(v)[:120]))
            hits += walk(v, path + '.' + k, depth + 1)
    elif isinstance(o, list):
        for i, v in enumerate(o[:12]):
            hits += walk(v, path + f'[{i}]', depth + 1)
    return hits

for f in [r'_p99_related.json', r'_p101_saves-after.json', r'_p102_commentA.json']:
    try:
        j = json.load(open(f, encoding='utf-8'))
    except Exception as e:
        print(f, 'ERR', e)
        continue
    print('=====', f)
    # 顶层 key
    print('top keys:', list(j.keys()) if isinstance(j, dict) else type(j))
    hits = walk(j)
    for h in hits[:20]:
        print('  SENS:', h)
    # profile 对象结构抽样
    def find_profiles(o, out, depth=0):
        if depth > 7 or len(out) > 4:
            return out
        if isinstance(o, dict):
            for k, v in o.items():
                if k in ('profile', 'author', 'creator', 'publisher') and isinstance(v, dict):
                    out.append((k, list(v.keys())))
                find_profiles(v, out, depth + 1)
        elif isinstance(o, list):
            for v in o[:20]:
                find_profiles(v, out, depth + 1)
        return out
    profs = find_profiles(j, [])
    for p in profs[:6]:
        print('  PROFILE', p)
print('DONE')
