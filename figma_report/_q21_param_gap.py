# -*- coding: utf-8 -*-
"""q21: 参数覆盖差集侦查 —— 已测参数集合 vs JS逆向候选参数集合（本地零请求）
Step1: 列出 q 脚本用途 docstring
Step2: 从历史测试脚本提取已打过的参数名（json={}/params={} key + URL query）
Step3: 从 figma_app-main.js 提取 API 上下文中的 snake_case 候选参数名
Step4: 差集（JS有 测试无）→ 输出待人工甄别的候选
"""
import sys, io, re, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DIR = r'D:\scan\figma_report'
JS_DIR = os.path.join(DIR, '_js')

# ---------- Step1: q 脚本用途 ----------
print('##### Step1: q 脚本 docstring #####')
for f in sorted(os.listdir(DIR)):
    if re.match(r'_figma_q\d+.*\.py$', f):
        p = os.path.join(DIR, f)
        try:
            head = open(p, encoding='utf-8', errors='ignore').read(400)
            m = re.search(r'"""(.{0,150}?)"""', head, re.S)
            print(f'  {f}: {m.group(1).strip() if m else "?"}')
        except Exception as e:
            print(f'  {f}: ERR {e}')

# ---------- Step2: 已测参数集合 ----------
tested = set()
urls_seen = set()
script_count = 0
for f in os.listdir(DIR):
    if not f.endswith('.py'):
        continue
    if not (f.startswith('_figma_') or f.startswith('_tmp_') or f.startswith('_q') or f.startswith('_et')):
        continue
    script_count += 1
    try:
        txt = open(os.path.join(DIR, f), encoding='utf-8', errors='ignore').read()
    except Exception:
        continue
    # json={'key': ...} / params={'key': ...} / data={'key': ...} / 直接 dict 字面量中的 'key':
    for m in re.finditer(r"""["']([a-z][a-z0-9_]{1,40})["']\s*:""", txt):
        tested.add(m.group(1))
    # URL 中 query 参数 ?a=b&c=d
    for m in re.finditer(r"""https?://[^"'\s]+?\?([a-z0-9_=&%.\[\]-]+)""", txt, re.I):
        for kv in m.group(1).split('&'):
            k = kv.split('=')[0]
            if re.match(r'^[a-z][a-z0-9_]*', k, re.I):
                tested.add(k.lower())
    # URL 模板观察
    for m in re.finditer(r"""/api/[A-Za-z0-9_/${}.\-]{2,80}""", txt):
        urls_seen.add(m.group(0).split('?')[0])

print(f'\n##### Step2: 已测参数集合（{script_count} 个脚本，{len(tested)} 个标识符） #####')
print(f'  API URL 观察 {len(urls_seen)} 个')

# ---------- Step3: JS 候选参数名 ----------
# 提取所有 snake_case 标识符（JS 中作为字符串 key 出现的）
js_files = ['figma_app-main.js']
snake = set()
for jf in js_files:
    p = os.path.join(JS_DIR, jf)
    if not os.path.exists(p):
        print(f'  [skip] {jf} not found')
        continue
    js = open(p, encoding='utf-8', errors='ignore').read()
    # snake_case 字符串 key/引号内标识符
    for m in re.finditer(r"""["'`]([a-z][a-z0-9]*_[a-z0-9_]{1,40})["'`]""", js):
        snake.add(m.group(1))
    # 对象字面量裸 key: xxx_yyy: 形式
    for m in re.finditer(r"""[,{]\s*([a-z][a-z0-9]*_[a-z0-9_]{1,40})\s*:""", js):
        snake.add(m.group(1))

print(f'\n##### Step3: JS snake_case 候选（figma_app-main.js）{len(snake)} 个 #####')

# ---------- Step4: 差集 ----------
gap = sorted(s for s in snake if s not in tested)
# 过滤明显非参数的（css类名遗迹少，snake_case 多半是参数名/枚举值；仍需人工甄别）
print(f'\n##### Step4: 差集（JS有、测试脚本字面未出现）{len(gap)} 个 #####')
for s in gap:
    print('  ', s)

# 落盘
with open(os.path.join(DIR, '_q21_gap.json'), 'w', encoding='utf-8') as fh:
    json.dump({'tested_count': len(tested), 'gap': gap}, fh, ensure_ascii=False, indent=1)
print('\nsaved: _q21_gap.json')
