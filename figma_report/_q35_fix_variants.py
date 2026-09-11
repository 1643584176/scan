# -*- coding: utf-8 -*-
"""q35: 对账口径修正 — camel/snake 形态归一后重算 used/never，修正 q34 分层
输出更新: Figma-从未用过的入参清单-2026-09-11.md + _q35_result.json
"""
import io, re, sys, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
DIR = r'D:\scan\figma_report'

def snake(k):
    return re.sub(r'([A-Z]+)', lambda m: '_' + m.group(1).lower(), k).lstrip('_')

d31 = json.load(io.open(os.path.join(DIR, '_q31b_result.json'), encoding='utf-8'))
res26 = json.load(io.open(os.path.join(DIR, '_q26_gap_result.json'), encoding='utf-8'))
d34 = json.load(io.open(os.path.join(DIR, '_q34_result.json'), encoding='utf-8'))

S = set(res26['S_filtered'])
used = set(d31['used_L1'])

uv = set()
for k in used:
    uv.add(k); uv.add(snake(k))

def is_used(k):
    return k in uv or snake(k) in uv

never_v2 = sorted(k for k in S if not is_used(k))
fake_never = sorted(set(d31['never_L1']) - set(never_v2))
print(f'S={len(S)}  used={len(used)}  used∩S={len([k for k in S if is_used(k)])}')
print(f'never_v2={len(never_v2)}  (旧 never_L1=1157, 假 never={len(fake_never)})')
print('\n=== 假 never 全量（snake 形态实际发送过） ===')
for k in fake_never:
    print(f'  {k}  (snake={snake(k)})')

nv2 = set(never_v2)
toapi2 = [k for k in d34['toapi'] if k in nv2]
win2 = [k for k in d34['win'] if k in nv2]
state2 = [k for k in d34['state'] if k in nv2]
print(f'\ntoAPI2={len(toapi2)}  win2={len(win2)}  state2={len(state2)}')

# ---- 重写 md ----
out = []
out.append('# Figma 从未用过的入参清单（动作级，q35 形态归一修正版）')
out.append('')
out.append(f'- 服务端参数全集 S: {len(S)}')
out.append(f'- 实际发送过的入参（脚本提取，共 {len(used)} 个）')
out.append(f'- 其中在 S 内（形态归一后）: **{len(S) - len(never_v2)}**')
out.append(f'- **从未发送过（修正后）: {len(never_v2)}**')
out.append(f'  - toAPI 层（请求构造链内，最可信）: {len(toapi2)}')
out.append(f'  - win/winq 层（API URL 调用点窗口）: {len(win2)}')
out.append(f'  - state 层（无 API 上下文）: {len(state2)}')
out.append('')
out.append('## 一、toAPI 层（真实参数，从未发送）——建议优先打')
out.append('')
attach = d34['attach']
for k in toapi2:
    a = attach.get(k, '')
    out.append(f'- `{k}` {("→ " + a) if a else ""}')
out.append('')
out.append(f'## 二、win 层（{len(win2)}，有 API 上下文）')
out.append('')
for k in win2:
    out.append(f'- `{k}`')
out.append('')
out.append(f'## 三、state 层（{len(state2)}，疑 UI/状态，见 json）')
out.append('')
out.append(f'## 假 never（snake 形态已打过，camel 形态在 JS 中，{len(fake_never)} 个）')
out.append('')
for k in fake_never:
    out.append(f'- `{k}` ↔ `{snake(k)}`（已发送）')
md = '\n'.join(out)
io.open(os.path.join(DIR, 'Figma-从未用过的入参清单-2026-09-11.md'), 'w', encoding='utf-8').write(md)

json.dump({'never_v2': never_v2, 'fake_never': fake_never, 'toapi2': toapi2, 'win2': win2, 'state2': state2},
          io.open(os.path.join(DIR, '_q35_result.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\nsaved: Figma-从未用过的入参清单-2026-09-11.md + _q35_result.json')
