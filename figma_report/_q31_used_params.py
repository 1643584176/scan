# -*- coding: utf-8 -*-
"""q31: 「已用入参」全量提取（动作级）vs 服务端参数全集 对账
- used_L1: URL查询串参数名([?&]name=) + 请求字典(params/json/data/payload/body/form)键 + Q() kwargs
- used_L2: used_L1 + 脚本内全部 'key': 字面量（宽泛参照层）
- S: _q26_gap_result.json 的 S_filtered（1286，服务端参数全集）
输出: 统计 + Figma-已用入参清单与未用入参-2026-09-11.md + _q31_result.json
"""
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
KEYRE = re.compile(r'[,{]\s*[\'"]?([a-zA-Z_][a-zA-Z0-9_]{2,40})[\'"]?\s*:')
for f in files:
    t = read(f)
    for m in re.finditer(r'[?&]([a-zA-Z_][a-zA-Z0-9_]{1,40})=', t):
        k = m.group(1); A[k] += 1; A_src.setdefault(k, f)
    for m in re.finditer(r'\b(?:params|json|data|payload|body|form)\s*=\s*\{', t):
        block = balance(t, m.end() - 1)
        for km in KEYRE.finditer(block):
            k = km.group(1); B[k] += 1; B_src.setdefault(k, f)
    for m in re.finditer(r'\bQ\(([^)]{0,400})\)', t):
        for km in re.finditer(r'([a-zA-Z_][a-zA-Z0-9_]{2,40})\s*=', m.group(1)):
            k = km.group(1); B[k] += 1; B_src.setdefault(k, f)
    for m in re.finditer(r'[\'"]([a-zA-Z_][a-zA-Z0-9_]{2,40})[\'"]\s*:', t):
        Cq[m.group(1)] += 1

used_L1 = set(A) | set(B)
used_L2 = used_L1 | set(Cq)
print(f'A(URL查询串): {len(A)}  B(请求字典/kwargs): {len(B)}  C(全字面量): {len(Cq)}')
print(f'used_L1: {len(used_L1)}   used_L2: {len(used_L2)}')

res26 = json.load(io.open('_q26_gap_result.json', encoding='utf-8'))
S = set(res26['S_filtered'])
gap_strict = set(res26['gap_strict'])
print('S:', len(S))

never_L1 = set(S) - used_L1
never_L2 = set(S) - used_L2
txt_but_never = sorted(never_L1 - gap_strict)     # 脚本/落盘文本出现过但从未作为入参发送
print(f'never_L1 (从未作为入参发送): {len(never_L1)}')
print(f'never_L2 (更严格): {len(never_L2)}')
print(f'脚本文本有但从未作为入参发送: {len(txt_but_never)}')

# 解析 q27 输出的 toAPI 标记
toapi = set()
t27 = read('_q27_out.txt')
for m in re.finditer(r'^-\s+(\S+)\s+\[([^\]]+)\]', t27, re.M):
    if 'toAPI' in m.group(2): toapi.add(m.group(1))
never_toapi = sorted(never_L1 & toapi)
print(f'toAPI 标记: {len(toapi)}  never_L1∩toAPI: {len(never_toapi)}')

# ---- 写 md ----
out = []
out.append('# Figma 已用入参清单与从未用过入参（q31 动作级对账）')
out.append('')
out.append(f'- 已用入参 L1（实际构造发送过的参数名）: **{len(used_L1)}**')
out.append(f'- 已用入参 L2（+脚本内宽泛字面量）: {len(used_L2)}')
out.append(f'- 服务端参数全集 S: {len(S)}')
out.append(f'- **从未作为入参发送（L1 判定）: {len(never_L1)}**')
out.append(f'- 其中「脚本/落盘文本出现过但从未发送」: {len(txt_but_never)}')
out.append(f'- 其中「toAPI 高置信真参数从未发送」: {len(never_toapi)}')
out.append('')
out.append('来源: 706 个测试脚本。L1 = URL查询串([?&]name=) + params/json/data/payload/body/form 字典键 + Q() kwargs。')
out.append('')
out.append(f'## 一、已用入参全量清单（{len(used_L1)}，按使用频次降序）')
out.append('')
out.append('格式: `参数名` (查询串次数/字典次数) 首见脚本')
out.append('')
for k in sorted(used_L1, key=lambda x: (-(A[x] + B[x]), x)):
    src = A_src.get(k) or B_src.get(k) or ''
    out.append(f'- `{k}` ({A[k]}/{B[k]}) {src}')
out.append('')
out.append(f'## 二、脚本/落盘文本出现过但从未作为入参发送（{len(txt_but_never)}）')
out.append('')
for k in txt_but_never:
    out.append(f'- `{k}`')
out.append('')
out.append(f'## 三、toAPI 高置信真参数从未发送（{len(never_toapi)}）')
out.append('')
for k in never_toapi:
    out.append(f'- `{k}`')
out.append('')
out.append(f'## 四、完全未发送的剩余部分（{len(never_L1) - len(txt_but_never)} 个，含 gap_never 全集）')
out.append('')
out.append('索引: `Figma-从未出现参数清单-2026-09-11.md`（已按 9 类分好）+ `_q31_result.json`（机器可读全量）')
out.append('')
out.append('### never_L2 更严格层（连脚本字面量都没有）')
out.append('')
out.append(f'数量: {len(never_L2)}，清单见 `_q31_result.json`')
md = '\n'.join(out)
io.open('Figma-已用入参清单与未用入参-2026-09-11.md', 'w', encoding='utf-8').write(md)

save = {
 'used_L1': sorted(used_L1),
 'used_L1_freq': {k: [A[k], B[k]] for k in used_L1},
 'used_L2': sorted(used_L2),
 'never_L1': sorted(never_L1),
 'never_L2': sorted(never_L2),
 'txt_but_never': txt_but_never,
 'never_toapi': never_toapi,
}
json.dump(save, io.open('_q31_result.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\nsaved: Figma-已用入参清单与未用入参-2026-09-11.md + _q31_result.json')
print('\n=== used_L1 高频 top 40 ===')
for k in sorted(used_L1, key=lambda x: -(A[x] + B[x]))[:40]:
    print(f'  {k}  ({A[k]}/{B[k]})')
