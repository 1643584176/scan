# -*- coding: utf-8 -*-
import io
p = r'D:\scan\_run_v63.py'
s = io.open(p, encoding='utf-8').read()
s = s.replace("GUEST = 'vda62_chroot_guest.py'", "GUEST = 'vda63_race_guest.py'")
s = s.replace("NAME = 'v62'", "NAME = 'v63'")
s = s.replace('/tmp/v62_stdout.log', '/tmp/v63_stdout.log')
s = s.replace('v62m.out', 'v63m.out')
s = s.replace('v62c.out', 'v63c.out')
s = s.replace('v62c2.out', 'v63c2.out')
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('DONE')
