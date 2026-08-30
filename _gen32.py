# -*- coding: utf-8 -*-
src = open('_run_v19f.py', encoding='utf-8').read()
# 升级: 每轮完整落盘
src = src.replace(
    "        tail = (r or '').replace('\\\\n', ' ')[-250:]",
    "        tail = (r or '').replace('\\\\n', ' ')[-250:]")
src = src.replace(
    "        if attempt in (1, 5, 12) and c != 200:",
    "        dumpfn = os.path.join(r'F:\\\\scan\\\\skills\\\\out', '%s_partial_%d.txt' % (GUEST.replace('.py', ''), attempt))\n"
    "        open(dumpfn, 'w', encoding='utf-8').write(r or '')\n"
    "        if attempt in (1, 5, 12) and c != 200:")
src = src.replace('v19f', 'v32s').replace('vda19_exec_chain_guest.py', 'vda32_celld_plugin_guest.py').replace('V19F_DONE', 'V32S_DONE')
open('_run_v32s.py', 'w', encoding='utf-8').write(src)
print('gen ok')
