# -*- coding: utf-8 -*-
src = open('_run_v37s.py', encoding='utf-8').read()
src = src.replace('v37s', 'v38s').replace('vda37_ctrd_create4_guest.py', 'vda38_ctrd_create5_guest.py').replace('V37S_DONE', 'V38S_DONE')
# 增加 sandbox_stopped 检测: 提前保存退出
src = src.replace(
    "        if c == 200 and MARK in r:",
    "        if 'sandbox_stopped' in (r or ''):\n"
    "            fn2 = os.path.join(r'F:\\scan\\skills\\out', '%s_stopped_%s.txt' % (GUEST.replace('.py', ''), time.strftime('%Y%m%d_%H%M%S')))\n"
    "            open(fn2, 'w', encoding='utf-8').write(r)\n"
    "            print('SANDBOX STOPPED - saved', fn2, flush=True)\n"
    "            break\n"
    "        if c == 200 and MARK in r:")
open('_run_v38s.py', 'w', encoding='utf-8').write(src)
print('gen ok')
