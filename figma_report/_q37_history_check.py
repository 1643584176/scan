# -*- coding: utf-8 -*-
import io, re, sys, os, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
os.chdir(r'D:\scan\figma_report')

print('=== 1) home_shelf / pinned 在测试脚本中的痕迹 ===')
for pat in ['home_shelf', 'resources/pinned', 'pinned']:
    print(f'--- pat {pat!r}:')
    for f in sorted(glob.glob('_figma_*.py') + glob.glob('_tmp_*.py') + glob.glob('_ai*.py')):
        if re.match(r'_q\d', f): continue
        try: t = io.open(f, encoding='utf-8', errors='replace').read()
        except Exception: continue
        if pat in t:
            ctx = [ln.strip()[:150] for ln in t.splitlines() if pat in ln][:2]
            print(f'  [{f}]')
            for c in ctx: print(f'     {c}')

print()
print('=== 2) 总账文档里的 pinned/home_shelf 结论 ===')
for f in glob.glob('*总账*.md') + glob.glob('Figma-SQL*.md'):
    t = io.open(f, encoding='utf-8', errors='replace').read()
    for pat in ['home_shelf', 'pinned', 'seen_resource', 'seenResource']:
        idxs = [m.start() for m in re.finditer(pat, t)]
        if idxs:
            print(f'[{f}] {pat} x{len(idxs)}')
            for i in idxs[:3]:
                print('   ', t[max(0, i-80):i+120].replace('\n', ' '))

print()
print('=== 3) 账号配置摘要 ===')
t = io.open('_figma_creds.py', encoding='utf-8', errors='replace').read()
for ln in t.splitlines():
    if '=' in ln and not ln.strip().startswith('#'):
        k = ln.split('=')[0].strip()
        v = ln.split('=', 1)[1].strip()
        if len(v) > 18: v = v[:14] + '...'
        print(f'  {k} = {v}')
