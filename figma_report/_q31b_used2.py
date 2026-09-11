# -*- coding: utf-8 -*-
"""q31b: 补充提取 json.dumps({...}) 与 dict(...) kwargs 形态，重建 used/never 对账"""
import io, re, sys, os, json, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
os.chdir(r'D:\scan\figma_report')

def read(p):
    try: return io.open(p, encoding='utf-8', errors='replace').read()
    except Exception: return ''

def balance(t, start):
    i = start; depth = 0; ln = len(t)
    while i < ln:
        c = t[i]
        if c in '"\'':
            q = c; i += 1
            while i < ln and t[i] != q:
                if t[i] == '\\': i += 1
                i += 1
        elif c == '{': depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0: return t[start:i+1]
        i += 1
    return t[start:start + 2000]

files = [f for f in os.listdir('.') if f.endswith('.py') and
         (f.startswith('_figma_') or f.startswith('_tmp_')) and not re.match(r'_q\d', f)]
print('脚本数:', len(files))

A = collections.Counter(); B = collections.Counter(); Cq = collections.Counter()
A_src = {}; B_src = {}
KEYRE = re.compile(r'[,{(]\s*[\'"]?([a-zA-Z_][a-zA-Z0-9_]{2,40})[\'"]?\s*[:=]')
for f in files:
    t = read(f)
    # A: URL 查询串
    for m in re.finditer(r'[?&]([a-zA-Z_][a-zA-Z0-9_]{1,40})=', t):
        k = m.group(1); A[k] += 1; A_src.setdefault(k, f)
    # B1: 请求上下文字典
    for m in re.finditer(r'\b(?:params|json|data|payload|body|form)\s*=\s*\{', t):
        block = balance(t, m.end() - 1)
        for km in KEYRE.finditer(block):
            k = km.group(1); B[k] += 1; B_src.setdefault(k, f)
    # B2: json.dumps({...})
    for m in re.finditer(r'json\.dumps\(\s*\{', t):
        block = balance(t, m.end() - 1)
        for km in KEYRE.finditer(block):
            k = km.group(1); B[k] += 1; B_src.setdefault(k, f)
    # B3: dict(kwargs) 形态
    for m in re.finditer(r'\bdict\(([^)]{0,800})\)', t):
        for km in re.finditer(r'([a-zA-Z_][a-zA-Z0-9_]{2,40})\s*=', m.group(1)):
            k = km.group(1); B[k] += 1; B_src.setdefault(k, f)
    # B4: Q() kwargs
    for m in re.finditer(r'\bQ\(([^)]{0,400})\)', t):
        for km in re.finditer(r'([a-zA-Z_][a-zA-Z0-9_]{2,40})\s*=', m.group(1)):
            k = km.group(1); B[k] += 1; B_src.setdefault(k, f)
    # C: 全字面量
    for m in re.finditer(r'[\'"]([a-zA-Z_][a-zA-Z0-9_]{2,40})[\'"]\s*:', t):
        Cq[m.group(1)] += 1

used_L1 = set(A) | set(B)
used_L2 = used_L1 | set(Cq)
print(f'A: {len(A)}  B: {len(B)}  C: {len(Cq)}')
print(f'used_L1: {len(used_L1)}   used_L2: {len(used_L2)}')

res26 = json.load(io.open('_q26_gap_result.json', encoding='utf-8'))
S = set(res26['S_filtered'])
gap_strict = set(res26['gap_strict'])
never_L1 = set(S) - used_L1
never_L2 = set(S) - used_L2
txt_but_never = sorted(never_L1 - gap_strict)
print(f'never_L1: {len(never_L1)}  never_L2: {len(never_L2)}  txt_but_never: {len(txt_but_never)}')

toapi = set()
t27 = read('_q27_out.txt')
for m in re.finditer(r'^-\s+(\S+)\s+\[([^\]]+)\]', t27, re.M):
    if 'toAPI' in m.group(2): toapi.add(m.group(1))
never_toapi = sorted(never_L1 & toapi)
print(f'never_L1∩toAPI: {len(never_toapi)}')

# ---- md ----
out = []
out.append('# Figma 已用入参清单与从未用过入参（q31b 动作级对账）')
out.append('')
out.append(f'- 已用入参 L1（实际构造发送过）: **{len(used_L1)}**')
out.append(f'- 已用入参 L2（+脚本宽泛字面量）: {len(used_L2)}')
out.append(f'- 服务端参数全集 S: {len(S)}')
out.append(f'- **从未作为入参发送（L1）: {len(never_L1)}**')
out.append(f'- 其中「文本出现过但从未发送」: {len(txt_but_never)}')
out.append(f'- 其中「toAPI 真参数从未发送」: {len(never_toapi)}')
out.append('')
out.append('提取源: 706 个测试脚本。L1 = URL查询串 + params/json/data 字典 + json.dumps({}) + dict(kwargs) + Q()。')
out.append('')
out.append(f'## 一、已用入参全量（{len(used_L1)}，按频次降序）')
out.append('')
out.append('格式: `参数名` (查询串次数/字典次数)')
out.append('')
for k in sorted(used_L1, key=lambda x: (-(A[x] + B[x]), x)):
    out.append(f'- `{k}` ({A[k]}/{B[k]})')
out.append('')
out.append(f'## 二、文本出现过但从未作为入参发送（{len(txt_but_never)}）')
out.append('')
for k in txt_but_never:
    out.append(f'- `{k}`')
out.append('')
out.append(f'## 三、toAPI 真参数从未发送（{len(never_toapi)}）')
out.append('')
for k in never_toapi:
    out.append(f'- `{k}`')
out.append('')
out.append(f'## 四、剩余完全未发送（{len(never_L1) - len(txt_but_never)}）')
out.append('')
out.append('见 `Figma-从未出现参数清单-2026-09-11.md` 分类 + `_q31b_result.json`')
md = '\n'.join(out)
io.open('Figma-已用入参清单与未用入参-2026-09-11.md', 'w', encoding='utf-8').write(md)

json.dump({
 'used_L1': sorted(used_L1),
 'used_L1_freq': {k: [A[k], B[k]] for k in used_L1},
 'used_L2': sorted(used_L2),
 'never_L1': sorted(never_L1),
 'never_L2': sorted(never_L2),
 'txt_but_never': txt_but_never,
 'never_toapi': never_toapi,
}, io.open('_q31b_result.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\nsaved: Figma-已用入参清单与未用入参-2026-09-11.md + _q31b_result.json')

print('\n=== used_L1 top 60 ===')
for k in sorted(used_L1, key=lambda x: -(A[x] + B[x]))[:60]:
    print(f'  {k} ({A[k]}/{B[k]})')
