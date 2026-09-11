# -*- coding: utf-8 -*-
# q58: 核查「校验器解析不了」字符家族历史覆盖（孤立代理/全角数字/非法UTF8/overlong/soft hyphen/Bidi/中段NUL/参数名异字节）
import sys, io, glob, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

d = r'D:\scan\figma_report'
files = [f for f in glob.glob(os.path.join(d, '_*.py')) if '_q58' not in f]
print(f'扫描脚本数: {len(files)}')

pats = {
    'A. 孤立代理 d800/d8xx': r'(d800|D800|d8xx|%ED%A0|ed%a0|\\uD8|\\ud8)',
    'B. 全角数字 FF1x': r'(%EF%BC%9[0-9]|FF1[0-9]|ff1[0-9]|１|２|３)',
    'C. 阿拉伯数字 066x': r'(%D9%[0-9A-F]|0661|066[0-9])',
    'D. overlong %C0%AF': r'(c0%af|C0%AF|c0af|overlong)',
    'E. 非法字节 %FF/%FE': r'(%ff|%FF|%fe|%FE)',
    'F. 中段/前段 NUL (plan_id 前后)': r'plan_id.*%00|%00.*plan_id|=\x00',
    'G. soft hyphen 00AD': r'(00ad|00AD|%C2%AD)',
    'H. Bidi 202E/RLO': r'(202e|202E|%E2%80%AE|RLO)',
    'I. 参数名带 NUL/异字节': r'plan_id%00|plan_id%ff|%00=|%ff=',
    'J. 超长数字串(>100位)': r"('1'\s*\*\s*[0-9]{2,}|'\d{100,}')",
}
for name, p in pats.items():
    print(f'\n===== {name} =====')
    rx = re.compile(p)
    hits = 0
    for f in files:
        try:
            t = open(f, encoding='utf-8', errors='replace').read()
        except Exception:
            continue
        for i, line in enumerate(t.splitlines(), 1):
            if rx.search(line):
                hits += 1
                if hits <= 8:
                    print(f'  {os.path.basename(f)}:{i}: {line.strip()[:140]}')
    print(f'  → 命中行数: {hits}')
print('\nDONE q58')
