# -*- coding: utf-8 -*-
"""q34: 「从未用过的入参」1157 个全量打来源标记（toAPI/win/winq/state）+ toAPI 层端点归属
输出: Figma-从未用过的入参清单-2026-09-11.md + _q34_result.json
"""
import io, re, sys, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DIR = r'D:\scan\figma_report'
JS_DIR = os.path.join(DIR, '_js')

def read(p):
    try: return io.open(p, encoding='utf-8', errors='replace').read()
    except Exception: return ''

d = json.load(io.open(os.path.join(DIR, '_q31b_result.json'), encoding='utf-8'))
never_L1 = d['never_L1']
print(f'never_L1: {len(never_L1)}')
nset = set(never_L1)

# ---- 重扫 JS 打来源标记 ----
src_of = {k: set() for k in nset}
CALL = re.compile(r'to(?:API|Query|Body)Parameters\(\s*\{')
js_files = [f for f in os.listdir(JS_DIR) if f.endswith('.js')]
for jf in js_files:
    js = read(os.path.join(JS_DIR, jf))
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
            if k in nset: src_of[k].add('toAPI')
    for m in re.finditer(r'url[`"\'](/api/[^`"\']{2,120})[`"\']', js):
        win = js[m.end():m.end()+700]
        for km in re.finditer(r'[,{]\s*([a-zA-Z_][a-zA-Z0-9_]{2,40})\s*:', win):
            k = km.group(1)
            if k in nset: src_of[k].add('win')
        for km in re.finditer(r'[&?]([a-z][a-z0-9_]{2,40})=', win):
            k = km.group(1)
            if k in nset: src_of[k].add('winq')

toapi = sorted(k for k in nset if 'toAPI' in src_of[k])
winl = sorted(k for k in nset if not ('toAPI' in src_of[k]) and ('win' in src_of[k] or 'winq' in src_of[k]))
state = sorted(k for k in nset if not src_of[k])
print(f'toAPI: {len(toapi)}  win: {len(winl)}  state: {len(state)}')

# ---- toAPI 层端点归属 ----
URLP = re.compile(r'url[`"\']([^`"\']{3,250})[`"\']|url:"(/[^"]{3,250})"|url:\'(/[^\']{3,250})\'|`(/api/[^`]{3,250})`')
def near_url(js, pos, back=5000):
    seg = js[max(0, pos-back):pos]
    best = None
    for m in URLP.finditer(seg):
        u = m.group(1) or m.group(2) or m.group(3) or m.group(4)
        if u and ('/api/' in u or u.startswith('/')):
            best = u
    return re.sub(r'\$\{[^}]*\}', '{}', best)[:120] if best else None

attach = {}
js_cache = {}
for jf in js_files:
    js = js_cache.setdefault(jf, read(os.path.join(JS_DIR, jf)))
for k in toapi:
    for jf in js_files:
        js = js_cache[jf]
        if not js or k not in js: continue
        idx = 0
        found = None
        for m in CALL.finditer(js):
            block_start = m.end() - 1
            # 直接找 key 位置（简单化）
        # 简化: 搜索 key 出现位置，取第一个命中并做 near_url
        pos = js.find(k)
        while pos >= 0:
            pre = js[max(0, pos-2000):pos]
            if CALL.search(pre):
                u = near_url(js, pos)
                if u: found = (jf, u); break
            pos = js.find(k, pos + 1)
        if found: break
    if found:
        attach[k] = f'{found[0]} :: {found[1]}'

# ---- 类型名/UI 黑名单过滤（仅用于 md 提示分层） ----
TYPER = re.compile(r'^[A-Z][a-z]+(?:[A-Z][a-z]+)*$')
UIPAT = re.compile(r'^(backgroundColor|borderRadius|className|children|color|border|bottom|top|left|right|width|height|font|margin|padding|alt|array|author|authors|available|button|callback|acquire|action|access|after|before|body|cacheNonce)$', re.I)

# ---- 写 md ----
out = []
out.append('# Figma 从未用过的入参清单（动作级 q34）')
out.append('')
out.append(f'- 服务端参数全集 S: 1286')
out.append(f'- 实际发送过的入参: 227（其中在 S 内的 129）')
out.append(f'- **从未发送过: {len(never_L1)}**')
out.append(f'  - toAPI 层（请求构造链内，最可信）: {len(toapi)}')
out.append(f'  - win/winq 层（API URL 调用点窗口）: {len(winl)}')
out.append(f'  - state 层（无 API 上下文，疑 UI/状态字段）: {len(state)}')
out.append('')
out.append('## 一、toAPI 层（真实参数，从未发送）——建议优先打')
out.append('')
for k in toapi:
    a = attach.get(k, '')
    out.append(f'- `{k}` {("→ " + a) if a else ""}')
out.append('')
out.append(f'## 二、win 层（{len(winl)}，有 API 上下文）')
out.append('')
for k in winl:
    out.append(f'- `{k}`')
out.append('')
out.append(f'## 三、state 层（{len(state)}，无 API 上下文，省略）')
out.append('')
out.append('清单见 `_q34_result.json`')
md = '\n'.join(out)
io.open(os.path.join(DIR, 'Figma-从未用过的入参清单-2026-09-11.md'), 'w', encoding='utf-8').write(md)

json.dump({'toapi': toapi, 'win': winl, 'state': state, 'attach': attach},
          io.open(os.path.join(DIR, '_q34_result.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\nsaved: Figma-从未用过的入参清单-2026-09-11.md + _q34_result.json')
print('\n=== toAPI 层全量 ===')
for k in toapi:
    print(f'  {k} {("→ " + attach.get(k, "")) if attach.get(k) else ""}')
