# -*- coding: utf-8 -*-
# 提取所有 _figma_r*.py 头部注释(面清单) + 统计各轮输出
import io, re, os, glob
d = os.path.dirname(os.path.abspath(__file__))
fs = sorted(glob.glob(os.path.join(d, '_figma_r*.py')))
# 按 r 编号数字排序
def rnum(f):
    m = re.search(r'_figma_r(\d+)', os.path.basename(f))
    return int(m.group(1)) if m else 0
fs.sort(key=rnum)
out = []
for f in fs:
    bn = os.path.basename(f)
    try:
        lines = io.open(f, encoding='utf-8', errors='replace').read().split('\n')[:4]
    except Exception:
        continue
    # 找注释行
    cmt = ' '.join(l.strip('# ').strip() for l in lines if l.strip().startswith('#'))
    out.append('%-42s %s' % (bn, cmt[:150]))
io.open(os.path.join(d, '_g1_scripts.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('scripts:', len(fs))
