# -*- coding: utf-8 -*-
# r197d 分析: 精确定位 C10-12 与 C1 的差异块(找瞬态字段名→归一化→判定)
import re, json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def body(p):
    d = open(p, 'rb').read().split(b'\n', 1)
    return d[1] if len(d) > 1 else b''

c1 = body('_r197_C1_base.txt')
# 1) 找 token 类字段真实名
names = set(re.findall(rb'"([a-z_]*time_token)"', c1))
print('token 字段名:', [n.decode() for n in names], flush=True)

# 2) 动态字段候选: 用 C1 vs C1r_replay(同参重放,时间不同) 找出所有会变的字段
c1r = body('_r197_C1r_replay.txt')
dyn = set()
for m in re.finditer(rb'"([a-z_]+)":"([^"]{1,80})"', c1):
    k, v = m.group(1), m.group(2)
    v2 = re.search(rb'"%s":"([^"]{1,80})"' % re.escape(k), c1r)
    if v2 and v2.group(1) != v:
        dyn.add(k.decode())
print('C1 vs 重放的动态字段:', sorted(dyn), flush=True)

# 3) 用动态字段全归一化后比对
def norm(b):
    for k in sorted(dyn):
        b = re.sub(('"%s":"[^"]*"' % k).encode(), ('"%s":"X"' % k).encode(), b)
    return b

nc1 = norm(c1)
for f in ['C10_arith0', 'C10b_arith1', 'C11_frag', 'C12_quote', 'C2_ref', 'C6b_small']:
    b = norm(body('_r197_%s.txt' % f))
    ok = (b == nc1)
    print('%-14s norm_equal=%s len=%d/%d' % (f, ok, len(b), len(nc1)), flush=True)
    if not ok and abs(len(b) - len(nc1)) < 4000:
        i, n = 0, min(len(b), len(nc1))
        shown = 0
        while i < n and shown < 3:
            if b[i] != nc1[i]:
                j = i
                while j < n and b[j] != nc1[j]:
                    j += 1
                print('   @%d C1:...%r' % (i, nc1[max(0, i-40):j+40]), flush=True)
                print('   @%d %s:...%r' % (i, f, b[max(0, i-40):j+40]), flush=True)
                i = j
                shown += 1
            else:
                i += 1
