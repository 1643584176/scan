# -*- coding: utf-8 -*-
"""q22: 「已打面 × 未测参数」精确对账（本地零请求）
方法:
 A. JS 侧: 找 figma_app-main.js 中所有 url`/api/...` / 'url:"/api/..."' 调用点,
    取其后续窗口内的对象字面量 key(含 snake_case 与 camelCase) → 端点参数候选集
 B. 已测侧: 从历史测试脚本提取打过的参数标识符 + URL query 参数
 C. 归一化对账: camelCase <-> snake_case 双向匹配
 D. 输出: (1) JS 查询类端点中"从没测过"的候选面; (2) 已打/相关端点中"没测过"的参数候选
"""
import sys, io, re, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DIR = r'D:\scan\figma_report'
JS_DIR = os.path.join(DIR, '_js')

def camel_to_snake(s):
    return re.sub(r'([A-Z]+)', lambda m: '_' + m.group(1).lower(), s).lstrip('_')

UI_NOISE = {'type','id','name','key','value','data','url','path','query','mode','text','label',
            'width','height','x','y','top','left','right','bottom','color','size','index','index',
            'onClick','onClose','onChange','className','style','children','target','status','error'}
EVENT_SUFFIX = ('_started','_failed','_completed','_clicked','_viewed','_shown','_dismissed',
                '_rendered','_requested','_loaded','_opened','_closed','_entered','_cancelled')

# ---------- B: 已测参数集合 ----------
tested = set()
for f in os.listdir(DIR):
    if not f.endswith('.py'): continue
    if not (f.startswith('_figma_') or f.startswith('_tmp_') or f.startswith('_q') or f.startswith('_et')):
        continue
    try: txt = open(os.path.join(DIR, f), encoding='utf-8', errors='ignore').read()
    except Exception: continue
    for m in re.finditer(r"""["']([a-zA-Z][a-zA-Z0-9_]{1,40})["']\s*:""", txt):
        k = m.group(1)
        tested.add(k); tested.add(camel_to_snake(k))
    for m in re.finditer(r"""https?://[^"'\s]+?\?([a-zA-Z0-9_=&%.\[\]-]+)""", txt, re.I):
        for kv in m.group(1).split('&'):
            k = kv.split('=')[0].lower()
            tested.add(k); tested.add(camel_to_snake(k))
print(f'[B] tested identifiers: {len(tested)}')

# ---------- A: JS 端点→参数候选 ----------
js = open(os.path.join(JS_DIR, 'figma_app-main.js'), encoding='utf-8', errors='ignore').read()
ep_params = {}   # normalized endpoint -> set(params)

pat1 = re.compile(r'url`(/api/[^`]{2,120})`')
pat2 = re.compile(r'url:\s*[`"\'](/api/[^`"\']{2,120})[`"\']')
for pat in (pat1, pat2):
    for m in pat.finditer(js):
        ep = m.group(1)
        # 归一化 ${...} → {}
        epn = re.sub(r'\$\{[^}]*\}', '{}', ep).split('?')[0]
        win = js[m.end():m.end() + 900]
        # 对象字面量 key:  {key: 或 ,key:
        keys = set()
        for km in re.finditer(r'[,{]\s*([a-zA-Z_][a-zA-Z0-9_]{1,40})\s*:', win):
            k = km.group(1)
            if k in UI_NOISE: continue
            if any(k.endswith(s) or camel_to_snake(k).endswith(s) for s in EVENT_SUFFIX): continue
            keys.add(k); keys.add(camel_to_snake(k))
        # 直接 & 拼接的 query 形态: xxx=  (仅取前面 key)
        for km in re.finditer(r'[&?]([a-z][a-z0-9_]{2,40})=', win):
            k = km.group(1)
            keys.add(k); keys.add(camel_to_snake(k))
        ep_params.setdefault(epn, set()).update(keys)

# 只保留可能收参的（GET/GET分页/查询类）端点：过滤纯资源动作端点无参噪声也行——全保留，输出时标注
print(f'[A] endpoints with param candidates: {len(ep_params)}')

# ---------- D1: 未测参数候选（逐端点） ----------
interesting = []   # (endpoint, [uncovered params])
for ep, params in sorted(ep_params.items()):
    uncov = sorted(p for p in params if len(p) >= 3 and p not in tested and '_' in p or (len(p) >= 8))
    uncov = sorted(p for p in params if len(p) >= 3 and p not in tested)
    if uncov:
        interesting.append((ep, uncov))

total_uncov = sum(len(u) for _, u in interesting)
print(f'[D1] endpoints={len(interesting)}, total uncovered param candidates={total_uncov}')
print()
for ep, uncov in interesting:
    print(f'  {ep}')
    print(f'      -> {", ".join(uncov[:30])}')

with open(os.path.join(DIR, '_q22_gap.json'), 'w', encoding='utf-8') as fh:
    json.dump({ep: u for ep, u in interesting}, fh, ensure_ascii=False, indent=1)
print()
print('saved: _q22_gap.json')
