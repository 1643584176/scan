# -*- coding: utf-8 -*-
"""q27: gap_never 二次分类 + JS 来源取证（toAPI / url窗口 / 其他）"""
import sys, io, re, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DIR = r'D:\scan\figma_report'
JS_DIR = os.path.join(DIR, '_js')

res = json.load(open(os.path.join(DIR, '_q26_gap_result.json'), encoding='utf-8'))
gap_never = res['gap_never']
gap_strict = res['gap_strict']
only_extra = sorted(set(gap_strict) - set(gap_never))   # 逆向产出见过但测试未碰

def read(p):
    try: return open(p, encoding='utf-8', errors='ignore').read()
    except Exception: return ''

# ---- 重扫 JS，只对 gap 取来源标记 ----
gap_all = set(gap_never) | set(only_extra)
src_of = {k: set() for k in gap_all}
js_files = [f for f in os.listdir(JS_DIR) if f.endswith('.js')]

CALL = re.compile(r'to(?:API|Query|Body)Parameters\(\s*\{')
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
            if k in gap_all: src_of[k].add('toAPI')
    for m in re.finditer(r'url[`"\'](/api/[^`"\']{2,120})[`"\']', js):
        win = js[m.end():m.end()+700]
        for km in re.finditer(r'[,{]\s*([a-zA-Z_][a-zA-Z0-9_]{2,40})\s*:', win):
            k = km.group(1)
            if k in gap_all: src_of[k].add('win')
        for km in re.finditer(r'[&?]([a-z][a-z0-9_]{2,40})=', win):
            k = km.group(1)
            if k in gap_all: src_of[k].add('winq')

def fmt(k):
    s = src_of.get(k, set())
    tag = '+'.join(sorted(s)) if s else 'state'
    return f'{k} [{tag}]'

# ---- 过滤 TS 类型名（大写开头，无下划线驼峰视为类型） ----
types = [k for k in gap_never if re.match(r'^[A-Z][a-zA-Z0-9]*$', k)]
rest  = [k for k in gap_never if k not in types]

RULES = [
 ('A.计费/订阅/席位/额度', r'billing|subscription|charge|cost|invoice|seat|license|plan_|metering|refund|vat|payment|intent|subtotal|pricing|renewal|credit|allocation|bypass'),
 ('B.权限/角色/安全', r'permission|role[_\b]|^role|^can[A-Z]|admin|approv|sharing|audience|scim|sso|idp|mfa|^ip_|allowlist|sensitive|verification|access|authed|oauth|scope|private|enable'),
 ('C.组织/团队/工作区', r'org|team|invite|domain|host|rank|workspace'),
 ('D.文件/资源/模板/媒体', r'file|folder|resource|duplicat|trash|branch|library|template|thumb|blob|upload|image|sha|node|canvas|widget|prototype|asset|editor|draft'),
 ('E.集成/密钥/URL', r'secret|token|key$|_key|certificate|encryption|github|repo|git|url|ugit|provision|remote|extension|plugin|mcp|cms|weave'),
 ('F.用户/群组', r'user|group|profile|email|nickname|pronoun|legal|seat|member'),
 ('G.分享/协作者/链接', r'link|recipient|collaborator|shared|removed_|remove_|added_|editors|sources|recipients|pending'),
 ('H.时间/过期/计数', r'date|time|_at$|until|expiration|ttl|timestamp|expires|resets|^num|^n_|count|frequenc|total|times|max'),
]

cats = {name: [] for name, _ in RULES}
other = []
for k in rest:
    hit = False
    for name, rx in RULES:
        if re.search(rx, k, re.I):
            cats[name].append(k); hit = True
    if not hit:
        other.append(k)

out = []
out.append('# Figma 从未出现的参数清单（q26/q27 终盘对账）')
out.append('')
out.append(f'- 服务端参数全集（JS 提取，过滤噪声后）: {len(res["S_filtered"])}')
out.append(f'- 测试未接触（gap_strict）: {len(gap_strict)}')
out.append(f'- **从未出现（gap_never，含逆向产出/文档）: {len(gap_never)}**')
out.append(f'- 分类后剩余可读候选: {len(rest)}（TS 类型名 {len(types)} 除外）')
out.append('')
out.append('来源标记: `toAPI`=构造请求序列化器内 · `win`=API URL 调用点窗口内 · `winq`=窗口内 query 形态 · `state`=仅内部状态（疑非 API 参数）')
out.append('')
for name, _ in RULES:
    if not cats[name]: continue
    out.append(f'## {name} ({len(cats[name])})')
    out.append('')
    for k in sorted(cats[name]):
        out.append(f'- {fmt(k)}')
    out.append('')
out.append(f'## Z.其他 ({len(other)})')
out.append('')
for k in sorted(other):
    out.append(f'- {fmt(k)}')
out.append('')
out.append('## X.TS 类型名（排除类）')
out.append('')
out.append(' '.join(types))
out.append('')
out.append(f'## Y.逆向产出见过但所有测试未碰（{len(only_extra)}）')
out.append('')
for k in only_extra:
    out.append(f'- {fmt(k)}')

md = '\n'.join(out)
with open(os.path.join(DIR, 'Figma-从未出现参数清单-2026-09-11.md'), 'w', encoding='utf-8') as fh:
    fh.write(md)
print(md)
print('\nsaved: Figma-从未出现参数清单-2026-09-11.md')
