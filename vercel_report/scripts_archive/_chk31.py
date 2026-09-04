# -*- coding: utf-8 -*-
txt = open('_run_v31r_out.txt', encoding='utf-8', errors='replace').read()
i = txt.find('mount ret=0')
print(repr(txt[max(0, i - 50):i + 3000]))
