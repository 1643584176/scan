# -*- coding: utf-8 -*-
"""h1kit smoke test: exercise every module from F:\\scan cwd."""
import os
import sys

os.chdir(r'F:\scan')
sys.path.insert(0, r'F:\scan')

print('=== 1. import h1kit ===')
import h1kit
from h1kit import gitbash, h1data, net, scaffold
print('version:', h1kit.__version__)

print()
print('=== 2. gitbash ===')
print('is_gitbash:', gitbash.is_gitbash())
print('winpath(/tmp/x):', gitbash.winpath('/tmp/x'))
print('winpath(/c/Users/a):', gitbash.winpath('/c/Users/a'))
print('winpath(F:/scan):', gitbash.winpath('F:/scan'))
print('py_run_cmd:', gitbash.py_run_cmd('_x.py'))
hits = gitbash.pygrep(r'execute_read', r'F:\scan\h1kit', include=None, max_hits=5)
print('pygrep hits:', len(hits), hits[:2] if hits else '')
print('memo head:', gitbash.shell_memo().splitlines()[0])

print()
print('=== 3. h1data ===')
progs = h1data.load_dump()
print('dump programs:', len(progs))
rows = h1data.find_programs(keywords=['search'], exclude=['figma', 'box'],
                            quiet=True)
print('find(search) ->', len(rows))
if rows:
    print('first:', rows[0]['name'], rows[0]['handle'])
info = h1data.program_info('mongodb')
print('program_info(mongodb):', info and info['name'], info and info['offers_bounties'],
      'in_scope=', len(info['in_scope']) if info else 0)
print('program_info(nonexistent_xyz):', h1data.program_info('nonexistent_xyz_zzz'))
out = h1data.scope_assets('mongodb')
print('scope_assets head:', out.splitlines()[0] if out else '')

print()
print('=== 4. scaffold ===')
d = scaffold.make_report_dir('kitdemo')
print('report dir:', d, os.path.isdir(os.path.join(d, '_probes')))
p = scaffold.make_baseline_md('mongodb', researcher='xxbo', out_dir=d)
print('baseline written:', os.path.exists(p))
txt = open(p, encoding='utf-8').read()
print('baseline first line:', txt.splitlines()[0])
print('has in-scope table:', 'In-Scope Assets' in txt)
print('has TODO policy block:', 'TODO: paste full policy' in txt)

print()
print('=== 5. net (quick local-only) ===')
print('exit_ip:', net.exit_ip()[:60])
res = net.check_hosts(['raw.githubusercontent.com'], timeout=4)
print('check_hosts done:', res[0][1] if res else 'empty')

print()
print('ALL SMOKE TESTS DONE')
