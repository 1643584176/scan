# -*- coding: utf-8 -*-
import io, re, sys, os, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
os.chdir(r'D:\scan\figma_report')

files = sorted(set(glob.glob('_figma_*.py') + glob.glob('_tmp_*.py') + glob.glob('_figma_r*.py')))
files = [f for f in files if not (f.startswith('_q2') or f.startswith('_ai'))]
print(f'总脚本数: {len(files)}')

# 1) def Q 的定义
print('\n=== def Q / def q 定义（前 3 个样本） ===')
n = 0
for f in files:
    t = io.open(f, encoding='utf-8', errors='replace').read()
    m = re.search(r'def Q\([^\n]*\n(?:[^\n]*\n){0,6}', t)
    if m:
        print(f'--- {f}:')
        print(m.group(0)[:400])
        n += 1
        if n >= 3: break

# 2) 模式分布统计
pats = {
 'params={': r'params\s*=\s*\{',
 'json={': r'json\s*=\s*\{',
 'data={': r'data\s*=\s*\{',
 'Q(': r'\bQ\(',
 'qs= 字符串含?': r"'(?:[^']*[?&][a-z_]+=[^']*)'",
 'url含字面query': r'["\'][^"\']*[/?&][a-z_]+=[^"\'&]*["\']',
}
print('\n=== 模式分布（每模式命中的文件数/总次数） ===')
for name, rx in pats.items():
    nf = 0; nt = 0
    for f in files:
        t = io.open(f, encoding='utf-8', errors='replace').read()
        c = len(re.findall(rx, t))
        if c: nf += 1; nt += c
    print(f'{name:16s} files={nf:4d} hits={nt:5d}')
