# -*- coding: utf-8 -*-
txt = open('_run_v30q_out.txt', encoding='utf-8', errors='replace').read()
i = txt.find('v30q.out')
print(repr(txt[i:i + 3000]) if i >= 0 else 'no v30q.out ref')
