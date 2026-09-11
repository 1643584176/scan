# -*- coding: utf-8 -*-
# r197 对照2: 字段级 dump(folder_id/name/条数) + 与基线差异块性质
import json

def body(p):
    d = open(p, 'rb').read().split(b'\n', 1)
    return d[1] if len(d) > 1 else b''

print('===== A. 字段级: meta.files 条数/名字/ folder_id =====')
for f in ['C1_base', 'C2_ref', 'C3_arith', 'C4_frag', 'C6a_notexist', 'C6b_small', 'C1r_replay']:
    try:
        j = json.loads(body('_r197_%s.txt' % f).decode('utf-8'))
    except Exception as e:
        print(f, 'ERR', repr(e)[:80], flush=True); continue
    files = j.get('meta', {}).get('files', [])
    print(f, 'n=%d' % len(files),
          'folder_id=%r' % [x.get('folder_id') for x in files[:3]],
          'names=%r' % [x.get('name') for x in files[:2]], flush=True)

print('===== B. 差异块 vs 基线 C1(前 6 块, 各带 50 字上下文) =====')
c1 = body('_r197_C1_base.txt').decode('utf-8')
for f in ['C2_ref', 'C3_arith', 'C4_frag', 'C6a_notexist', 'C6b_small', 'C1r_replay']:
    try:
        b = body('_r197_%s.txt' % f).decode('utf-8')
    except Exception:
        continue
    diffs = []
    i = 0
    n = min(len(c1), len(b))
    while i < n and len(diffs) < 6:
        if c1[i] != b[i]:
            j = i
            while j < n and c1[j] != b[j]:
                j += 1
            diffs.append((i, c1[max(0, i - 50):j + 50], b[max(0, i - 50):j + 50]))
            i = j
        else:
            i += 1
    print('-- %s: len %d vs %d, blocks=%d' % (f, len(c1), len(b), len(diffs)), flush=True)
    for off, a, c in diffs:
        print('   @%d' % off, flush=True)
        print('     C1: ...%r' % a, flush=True)
        print('     %s: ...%r' % (f, c), flush=True)
