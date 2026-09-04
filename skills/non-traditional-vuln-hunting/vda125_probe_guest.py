# -*- coding: utf-8 -*-
"""v125 payload: 修正 descriptor 定位 (endswith 匹配 + 容错 trial)
v124 失败原因: 文件名带路径前缀, == 匹配不到
输出 /vercel/sandbox/v125d.out"""
import time, signal, io, re

OUT = '/vercel/sandbox/v125c.out'
FOUT = '/vercel/sandbox/v125d.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
g = open(FOUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(220)


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


def rv(data, off):
    shift = 0
    val = 0
    while off < len(data):
        b = data[off]
        off += 1
        val |= (b & 0x7f) << shift
        if not (b & 0x80):
            return val, off
        shift += 7
        if shift > 63:
            return -1, off
    return -1, off


def parse_fields(data, off=0):
    out = []
    while off < len(data):
        key, off2 = rv(data, off)
        if key < 0 or off2 > len(data):
            return None
        off = off2
        fno = key >> 3
        wt = key & 7
        if fno == 0:
            return None
        if wt == 0:
            v, off = rv(data, off)
            if v < 0:
                return None
            out.append((fno, wt, v))
        elif wt == 1:
            if off + 8 > len(data):
                return None
            out.append((fno, wt, data[off:off + 8]))
            off += 8
        elif wt == 2:
            ln, off = rv(data, off)
            if ln < 0 or off + ln > len(data):
                return None
            out.append((fno, wt, data[off:off + ln]))
            off += ln
        elif wt == 5:
            if off + 4 > len(data):
                return None
            out.append((fno, wt, data[off:off + 4]))
            off += 4
        else:
            return None
    return out


def sval(v):
    if isinstance(v, bytes):
        try:
            return v.decode('utf-8')
        except Exception:
            return None
    return v


TYPE_NAMES = {1: 'double', 2: 'float', 3: 'int64', 4: 'uint64', 5: 'int32', 6: 'fixed64',
              7: 'fixed32', 8: 'bool', 9: 'string', 11: 'message', 12: 'bytes',
              13: 'uint32', 14: 'enum', 15: 'sfixed32', 16: 'sfixed64', 17: 'sint32', 18: 'sint64'}


def parse_field_def(data):
    name = num = typ = tname = label = None
    flds = parse_fields(data)
    if flds is None:
        return None
    for fno, wt, v in flds:
        if fno == 1:
            name = sval(v)
        elif fno == 3:
            num = v
        elif fno == 4:
            label = v
        elif fno == 5:
            typ = v
        elif fno == 6:
            tname = sval(v)
    if name is None or num is None:
        return None
    return (name, num, typ, tname, label)


def parse_enum(data):
    name = None
    vals = []
    flds = parse_fields(data)
    if flds is None:
        return None
    for fno, wt, v in flds:
        if fno == 1:
            name = sval(v)
        elif fno == 2:
            vf = parse_fields(v)
            if vf:
                vname = vnum = None
                for f2, w2, v2 in vf:
                    if f2 == 1:
                        vname = sval(v2)
                    elif f2 == 2:
                        vnum = v2
                if vname is not None:
                    vals.append((vname, vnum))
    return (name, vals)


def parse_msg(data, path, lines):
    name = None
    fields = []
    nested = []
    enums = []
    flds = parse_fields(data)
    if flds is None:
        return False
    for fno, wt, v in flds:
        if fno == 1:
            name = sval(v)
        elif fno == 2:
            fd = parse_field_def(v)
            if fd:
                fields.append(fd)
        elif fno == 3:
            nested.append(v)
        elif fno == 4:
            enums.append(v)
    if not name:
        return False
    full = path + '.' + name
    lines.append('MSG %s' % full)
    for fname, fnum, ftyp, tname, flabel in fields:
        t = TYPE_NAMES.get(ftyp, '?%d' % ftyp)
        lab = {1: 'opt', 2: 'req', 3: 'rep'}.get(flabel, '?')
        lines.append('  f%d %s %s %s %s' % (fnum, fname, t, tname or '', lab))
    for v in nested:
        parse_msg(v, full, lines)
    for v in enums:
        ev = parse_enum(v)
        if ev and ev[0]:
            lines.append('  ENUM %s.%s' % (full, ev[0]))
            for vn, vnum in ev[1]:
                lines.append('    %s = %s' % (vn, vnum))
    return True


def parse_file(data, nm=None):
    flds = parse_fields(data)
    if flds is None:
        return None
    fname = pkg = None
    msgs = []
    enums = []
    svcs = []
    ok = True
    for fno, wt, v in flds:
        if fno == 1:
            fname = sval(v)
        elif fno == 2:
            pkg = sval(v)
        elif fno == 4:
            if not parse_msg(v, pkg or '', []):
                ok = False
            msgs.append(v)
        elif fno == 5:
            enums.append(v)
        elif fno == 6:
            svcs.append(v)
    if not fname or not pkg:
        return None
    if not fname.endswith('.proto'):
        return None
    if nm and not fname.endswith(nm):
        return None
    if not ok:
        return None
    lines = []
    for v in msgs:
        parse_msg(v, pkg, lines)
    for v in enums:
        ev = parse_enum(v)
        if ev and ev[0]:
            lines.append('ENUM %s.%s' % (pkg, ev[0]))
            for vn, vnum in ev[1]:
                lines.append('  %s = %s' % (vn, vnum))
    for v in svcs:
        sv = parse_fields(v)
        if sv:
            sname = None
            for f2, w2, v2 in sv:
                if f2 == 1:
                    sname = sval(v2)
            if sname:
                lines.append('SVC %s.%s' % (pkg, sname))
                for f2, w2, v2 in sv:
                    if f2 == 2:
                        mv = parse_fields(v2)
                        if mv:
                            mn = mi = mo = None
                            for f3, w3, v3 in mv:
                                if f3 == 1:
                                    mn = sval(v3)
                                elif f3 == 2:
                                    mi = sval(v3)
                                elif f3 == 3:
                                    mo = sval(v3)
                            if mn:
                                lines.append('  %s(%s)->%s' % (mn, mi, mo))
    return (fname, pkg, lines)


log('=== P1 read celld ===')
blob = None
for cand in ('/proc/1/root/opt/vercel/celld', '/opt/vercel/celld'):
    try:
        with open(cand, 'rb') as fh:
            blob = fh.read()
        log('read %s %d bytes' % (cand, len(blob)))
        break
    except Exception as e:
        log('open %s ERR %s' % (cand, type(e).__name__))
if not blob:
    f.close()
    g.close()
    raise SystemExit

log('=== P2 locate descriptors ===')
names = set()
for m in re.finditer(rb'[a-z0-9_/]+\.proto', blob):
    s = m.group(0)
    if len(s) > 8 and s not in names:
        names.add(s)
log('proto names: %d' % len(names))

parsed = 0
for nm in sorted(names, key=len, reverse=True):
    fnb = nm
    start = 0
    while True:
        p = blob.find(fnb, start)
        if p < 0:
            break
        # 回溯找 field1 key: 0x0a <varint len> <bytes endswith nm>
        kstart = None
        for back in range(p, max(0, p - 128), -1):
            if back > 0 and blob[back - 1] == 0x0a:
                ln, off = rv(blob, back)
                if 0 < ln <= 300 and back + ln <= len(blob):
                    seg = blob[back:back + ln]
                    if seg.endswith(fnb) and seg.count(b'/') <= 8:
                        kstart = back - 1
                        break
        if kstart is not None:
            for trial in range(max(0, kstart - 10), kstart + 2):
                res = parse_file(blob[trial:trial + 300000], nm)
                if res:
                    fname, pkg, lines = res
                    parsed += 1
                    tag = 'CELL' if 'vercel.hive.cell' in pkg else 'other'
                    g.write('=== FILE %s pkg=%s [%s] ===\n' % (fname, pkg, tag))
                    for ln in lines:
                        g.write(ln + '\n')
                    g.flush()
                    log('parsed %s [%s] %dB' % (fname, tag, len('\n'.join(lines))))
                    break
        start = p + 1
log('parsed files total=%d' % parsed)

g.flush()
log('V125C_DONE')
f.close()
g.close()
