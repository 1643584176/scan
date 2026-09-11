# -*- coding: utf-8 -*-
"""q38: 修正版 never 对账(含 L2 字面量口径+变体归一) + 候选端点历史痕迹核查"""
import io, re, sys, os, json, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
os.chdir(r'D:\scan\figma_report')

d26 = json.load(open('_q26_gap_result.json', encoding='utf-8'))
d31 = json.load(open('_q31b_result.json', encoding='utf-8'))
d35 = json.load(open('_q35_result.json', encoding='utf-8'))
d34 = json.load(open('_q34_result.json', encoding='utf-8'))

# --- 1) 修正版 never: 用 used_L2(454, 含全部字面量) + 变体归一 ---
S = set(d26['S_filtered'])
used_l2 = set(d31['used_L2'])

def snake(k):
    return re.sub(r'([A-Z]+)', lambda m: '_' + m.group(1).lower(), k).lstrip('_')

uv = set()
for k in used_l2:
    uv.add(k); uv.add(snake(k))

never_final = sorted(k for k in S if not (k in uv or snake(k) in uv))
print(f'[1] S={len(S)}  used_L2={len(used_l2)}  never_final={len(never_final)}')

# 与旧 never_v2 对比，剔除的伪 never
old_never = set(d35['never_v2'])
dropped = sorted(old_never - set(never_final))
print(f'    旧 never_v2={len(old_never)}  剔除伪 never={len(dropped)}')
print(f'    伪never样本: {dropped[:40]}')

# --- 2) never_final 与 q34 toAPI 标记(高风险集) ---
d34_toapi_keys = set(d34['toapi'])
toapi_never = sorted(set(d34_toapi_keys) & set(never_final))
print(f'[2] q34 toAPI标记键={len(d34_toapi_keys)}  其中仍未打={len(toapi_never)}')
for k in toapi_never: print('    ', k)

# --- 3) 候选端点历史痕迹核查 ---
print('[3] 历史测试痕迹:')
pats = ['hub_file_duplicates', 'tagged_file', 'make_libraries', 'ds_import_libraries',
        'videos/', 'notification_settings', 'reference_id', 'weave_cover_photo']
files = sorted(glob.glob('_figma_*.py') + glob.glob('_tmp_*.py') + glob.glob('_ai*.py'))
for pat in pats:
    hits = []
    for f in files:
        if re.match(r'_q\d', f) or f in ('_q36_candidates.py', '_q37_history_check.py'): continue
        try: t = io.open(f, encoding='utf-8', errors='replace').read()
        except Exception: continue
        if pat in t:
            n = t.count(pat)
            hits.append(f'{f}(x{n})')
    print(f'  {pat}: {hits[:8] if hits else "ZERO"}')

# --- 4) 落盘/产出目录里也有测试记录吗 ---
print('[4] 输出文件痕迹:')
for pat in pats:
    hits = []
    for f in glob.glob('_figma_*_out*.txt') + glob.glob('*.md'):
        if f in ('_q36_out.txt',): continue
        try: t = io.open(f, encoding='utf-8', errors='replace').read()
        except Exception: continue
        if pat in t: hits.append(f'({f})')
    print(f'  {pat}: {hits[:6] if hits else "ZERO"}')
