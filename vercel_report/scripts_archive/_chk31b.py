# -*- coding: utf-8 -*-
txt = open('_run_v31r_out.txt', encoding='utf-8', errors='replace').read()
i = txt.find('P1 lists')
print(repr(txt[max(0, i - 300):i + 2500]))
