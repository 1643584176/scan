# -*- coding: utf-8 -*-
# q80: page_thumbnails 历史覆盖 + JS 调用形态
import sys, io, glob, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

D = r'D:\scan\figma_report'
py = glob.glob(os.path.join(D, '_*.py'))
print('== A. 历史脚本中的 page_thumbnails ==')
for f in py:
    bn = os.path.basename(f)
    if bn.startswith(('_q80', '_r251', '_r253')): continue
    try: t = open(f, encoding='utf-8', errors='replace').read()
    except: continue
    for m in re.finditer(r'page_thumbnails', t):
        i = m.start()
        seg = t[max(0,i-100):i+150].replace('\n', ' ')
        print(f'  {bn}: ...{seg}...')
print('\n== B. 935 JS 里 page_thumbnails / updatePageCheckpointThumbnails 定义 ==')
t = open(os.path.join(D, '_js', '935-431f89677a39072c.min.js'), encoding='utf-8', errors='replace').read()
for kw in ['page_thumbnails', 'updatePageCheckpointThumbnails']:
    print(f'  -- {kw} --')
    for m in list(re.finditer(re.escape(kw), t))[:4]:
        i = m.start()
        print(f'    ...{t[max(0,i-160):i+220]!r}...'.replace(chr(92)+'n', ' '))
print('\n== C. videos thumbs 历史里用的方法形态 ==')
for f in py:
    bn = os.path.basename(f)
    try: t = open(f, encoding='utf-8', errors='replace').read()
    except: continue
    for m in list(re.finditer(r'videos/[^/]*/thumbnails|videos/\{[^}]*\}/thumbnails', t))[:2]:
        i = m.start()
        print(f'  {bn}: ...{t[max(0,i-120):i+120]}...'.replace('\n', ' '))
print('DONE q80')
