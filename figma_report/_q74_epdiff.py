# -*- coding: utf-8 -*-
# q74: 「端点差集」——JS 客户端里的全部 /api/ 端点 vs 历史脚本打过的端点
import sys, io, glob, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

D = r'D:\scan\figma_report'

# 1) JS 提取（935 主 API 客户端 + 全部 JS）
def js_endpoints(files):
    eps = {}
    rx1 = re.compile(r't\.url`(/api/[^`]+)`')
    rx2 = re.compile(r'"(/api/[a-z0-9_/{}\$\-]+)"')
    for f in files:
        try:
            t = open(f, encoding='utf-8', errors='replace').read()
        except Exception:
            continue
        for rx in (rx1, rx2):
            for m in rx.finditer(t):
                eps.setdefault(m.group(1), set()).add(os.path.basename(f))
    return eps

main = [os.path.join(D, '_js', '935-431f89677a39072c.min.js')]
js_eps = js_endpoints(main)
print(f'===== 935 主客户端里的 /api/ 端点: {len(js_eps)} 个 =====')

def norm(u):
    # 归一：数字段/大段 → {id}
    u = re.sub(r'/\$\{[^}]*\}', '/{id}', u)
    u = re.sub(r'/\d{6,}', '/{id}', u)
    u = re.sub(r'/[A-Za-z0-9_.\-]{10,}/', '/{key}/', u)
    return u

normed_js = {}
for u in js_eps:
    normed_js.setdefault(norm(u), set()).add(u)

# 2) 历史脚本打过的端点
hist = set()
hist_files = glob.glob(os.path.join(D, '_*.py'))
rx_h = re.compile(r'/(api/[a-z0-9_/\-]+)')
for f in hist_files:
    try:
        t = open(f, encoding='utf-8', errors='replace').read()
    except Exception:
        continue
    for m in rx_h.finditer(t):
        hist.add(m.group(1))
hist_normed = set(norm('/' + h) for h in hist)

print(f'\n===== 历史脚本涉及的端点前缀: {len(hist_normed)} 个（归一后） =====')

# 3) 差集：JS 有、历史没有（按归一模式对比 + 原始 URL 段对比）
print('\n===== 差集：JS 客户端有、历史脚本从未出现过 =====')
never = []
for n, origs in sorted(normed_js.items()):
    seg = n.strip('/').split('/')
    # 用"路径段签名"松散匹配：历史里是否出现同一段签名
    key_seg = [s for s in seg if not s.startswith('{')]
    found = False
    for h in hist:
        h_seg = set(h.split('/'))
        if all(s in h_seg for s in key_seg if s not in ('api',)):
            found = True
            break
    if not found:
        never.append((n, sorted(origs)[:2]))
for n, o in never:
    print(f'  {n}')
    for oo in o[:1]:
        print(f'      src: {oo[:110]}')
print(f'\n差集总数: {len(never)}')
print('DONE q74')
