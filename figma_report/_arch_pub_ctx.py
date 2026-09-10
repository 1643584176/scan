# -*- coding: utf-8 -*-
"""挖 community_publishers accept/remove + publisher 管理 的 HTTP 调用细节"""
import sys, io, re, glob, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

js_dir = r'D:\scan\figma_report\_js'

# 1) 在 9668 里找 accept/remove 的实际请求调用
for fname in ['9668-5317375f131d42d8.min.js', '7435-ce1dc6726292bd56.min.js']:
    fp = os.path.join(js_dir, fname)
    data = open(fp, encoding='utf-8', errors='ignore').read()
    print(f'########## FILE {fname} len={len(data)}')
    # 找所有 community_publishers 出现点
    for m in re.finditer(r'community_publishers', data):
        s = max(0, m.start() - 150)
        ctx = data[s:m.end() + 250]
        print(f'\n--- pos {m.start()} ---')
        print(ctx.replace('\n', ' ')[:400])

    # 找 accept / remove 调用(axios .post/.delete/.put 邻近)
    for m in re.finditer(r'\.(?:post|put|delete|get)\([^)]{0,120}?(?:publisher|accept|remove)[^)]{0,120}\)', data):
        s = max(0, m.start() - 200)
        print(f'\n--- CALL pos {m.start()} ---')
        print(data[s:m.end() + 200].replace('\n', ' ')[:450])
print('DONE')
