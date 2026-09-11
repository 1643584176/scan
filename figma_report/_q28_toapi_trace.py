# -*- coding: utf-8 -*-
"""q28: 从未出现参数中「toAPI 高置信」集的端点归属取证"""
import sys, io, re, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DIR = r'D:\scan\figma_report'
JS_DIR = os.path.join(DIR, '_js')

res = json.load(open(os.path.join(DIR, '_q26_gap_result.json'), encoding='utf-8'))
gap_never = set(res['gap_never'])

def read(p):
    try: return open(p, encoding='utf-8', errors='ignore').read()
    except Exception: return ''

CALL = re.compile(r'to(?:API|Query|Body)Parameters\(\s*\{')
param_hits = {}
js_cache = {}
js_files = [f for f in os.listdir(JS_DIR) if f.endswith('.js')]
for jf in js_files:
    js = read(os.path.join(JS_DIR, jf)); js_cache[jf] = js
    if not js: continue
    for m in CALL.finditer(js):
        start = m.end() - 1; i = start; depth = 0; ln = len(js)
        while i < ln:
            c = js[i]
            if c in '"\'':
                q = c; i += 1
                while i < ln and js[i] != q:
                    if js[i] == '\\': i += 1
                    i += 1
            elif c == '{': depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0: break
            i += 1
        block = js[start:i+1]
        for km in re.finditer(r'[,{]\s*([a-zA-Z_][a-zA-Z0-9_]{2,40})\s*:', block):
            k = km.group(1)
            if k in gap_never:
                param_hits.setdefault(k, []).append((jf, start + km.start()))

URLP = re.compile(r'url[`"\']([^`"\']{3,250})[`"\']|url:"(/[^"]{3,250})"|url:\'(/[^\']{3,250})\'|`(/api/[^`]{3,250})`')

def near_url(js, pos, back=5000):
    seg = js[max(0, pos-back):pos]
    best = None
    for m in URLP.finditer(seg):
        u = m.group(1) or m.group(2) or m.group(3) or m.group(4)
        if u and ('/api/' in u or u.startswith('/')):
            best = u
    if best:
        return re.sub(r'\$\{[^}]*\}', '{}', best)[:120]
    return None

print(f'toAPI 高置信参数数: {len(param_hits)}\n')
for k in sorted(param_hits):
    hits = param_hits[k]
    print(f'### {k}  (块内出现 {len(hits)} 次)')
    shown = set()
    for jf, pos in hits[:5]:
        js = js_cache[jf]
        u = near_url(js, pos)
        tag = f'{jf} :: {u}' if u else f'{jf} :: (前 5k 无 url)'
        if tag in shown: continue
        shown.add(tag)
        # 截取参数位点前后 80 字符作为样本
        seg = js[max(0, pos-60):pos+90].replace('\n', ' ')
        print(f'   - {tag}')
        print(f'     ctx: ...{seg}...')
    print()
