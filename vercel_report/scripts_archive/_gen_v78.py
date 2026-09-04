# -*- coding: utf-8 -*-
# 生成 v78 guest + 驱动 (基于 v76, 追加 celld proto 字段提取)
g = open(r'D:\scan\skills\non-traditional-vuln-hunting\vda76_guest.py', encoding='utf-8').read()
g = g.replace('vda76', 'vda78').replace('v76', 'v78').replace('V76C_DONE', 'V78C_DONE')

# 在 V66M_DONE 前插入 celld 分析 (提取 ContainersService 相关 proto 字段)
celld_analysis = '''    # === celld proto 字段提取 ===
    try:
        data = open('/mnt/vdax/opt/vercel/celld', 'rb').read()
        log('celld size=%d' % len(data))
        import re as _re
        strs = [s.decode('utf-8', 'replace') for s in _re.findall(rb'[\\x20-\\x7e]{4,}', data)]
        def dump(title, cond, lim=80):
            seen = set()
            n = 0
            log('--- %s ---' % title)
            for s in strs:
                if cond(s) and s not in seen and len(s) < 200:
                    seen.add(s)
                    log('  %s' % s[:180])
                    n += 1
                    if n >= lim:
                        break
            log('(%d shown)' % n)
        # StreamOutput/Stdin 相关上下文
        dump('STREAM-CTX', lambda s: 'Stream' in s or 'stream' in s or 'Output' in s or 'output' in s)
        dump('STDIN-CTX', lambda s: 'Stdin' in s or 'stdin' in s or 'Input' in s)
        dump('EXEC-CTX', lambda s: ('Exec' in s and len(s) < 120) or 'exec' in s)
        # 容器字段 (驼峰)
        dump('CTR-FIELDS', lambda s: _re.match(r'^[a-z][A-Za-z0-9_]{2,30}$', s) and any(
            k in s for k in ('Id', 'ID', 'Process', 'Container', 'Status', 'Output', 'Input')))
        # proto service/method 全名
        dump('SVC-METHOD', lambda s: bool(_re.match(r'^[A-Za-z0-9_.]+\\.[A-Za-z0-9_.]+/[A-Za-z0-9_]+$', s)))
    except Exception as e:
        log('celld analysis EXC %s' % e)
    log('V66M_DONE')
    f.close()'''

old_tail = """    log('V66M_DONE')
    f.close()"""
assert old_tail in g, 'tail not found'
g = g.replace(old_tail, celld_analysis)
open(r'D:\scan\skills\non-traditional-vuln-hunting\vda78_guest.py', 'w', encoding='utf-8').write(g)

d = open(r'D:\scan\_run_v76.py', encoding='utf-8').read()
d = d.replace('vda76', 'vda78').replace('v76', 'v78').replace('V76', 'V78')
open(r'D:\scan\_run_v78.py', 'w', encoding='utf-8').write(d)
print('done')
