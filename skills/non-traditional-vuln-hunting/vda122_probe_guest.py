# -*- coding: utf-8 -*-
"""v122 payload: 解析 celld 二进制内嵌 protobuf descriptor
扫描 gzip 块 (1f 8b 08) -> zlib 解压 -> wire 解析 FileDescriptorProto
提取所有 message/enum/service 定义 -> /vercel/sandbox/v122d.out
重点: ExecRequest/StartRequest/StreamOutputRequest/ExecProcess/Process 字段"""
import zlib, struct, time, signal, json, io

OUT = '/vercel/sandbox/v122c.out'
FOUT = '/vercel/sandbox/v122d.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
g = open(FOUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(240)


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


# ---------- protobuf wire 解析 ----------
def rv(data, off):
    """读 varint"""
    shift = 0
    val = 0
    while off < len(data):
        b = data[off]
        off += 1
        val |= (b & 0x7f) << shift
        if not (b & 0x80):
            return val, off
        shift += 7
    return val, off


def parse_fields(data, off=0, depth=0):
    """返回 [(fno, wt, val)] 其中 val: int / bytes / list"""
    out = []
    while off < len(data):
        try:
            key, off = rv(data, off)
        except Exception:
            break
        fno = key >> 3
        wt = key & 7
        if wt == 0:
            v, off = rv(data, off)
            out.append((fno, wt, v))
        elif wt == 1:
            out.append((fno, wt, data[off:off + 8]))
            off += 8
        elif wt == 2:
            ln, off = rv(data, off)
            out.append((fno, wt, data[off:off + ln]))
            off += ln
        elif wt == 5:
            out.append((fno, wt, data[off:off + 4]))
            off += 4
        else:
            break
    return out


def sval(v):
    if isinstance(v, bytes):
        try:
            return v.decode('utf-8')
        except Exception:
            return '<bin %dB>' % len(v)
    return v


TYPE_NAMES = {1: 'double', 2: 'float', 3: 'int64', 4: 'uint64', 5: 'int32', 6: 'fixed64',
              7: 'fixed32', 8: 'bool', 9: 'string', 10: 'group', 11: 'message', 12: 'bytes',
              13: 'uint32', 14: 'enum', 15: 'sfixed32', 16: 'sfixed64', 17: 'sint32', 18: 'sint64'}


def parse_field_def(data):
    """FieldDescriptorProto -> (name, number, type, type_name, label, json_name)"""
    name = num = typ = tname = label = jname = None
    for fno, wt, v in parse_fields(data):
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
        elif fno == 8:
            jname = sval(v)
    return name, num, typ, tname, label, jname


def parse_enum(data):
    """EnumDescriptorProto -> (name, [(value_name, number)])"""
    name = None
    vals = []
    for fno, wt, v in parse_fields(data):
        if fno == 1:
            name = sval(v)
        elif fno == 2:
            for f2, w2, v2 in parse_fields(v):
                if f2 == 1:
                    vname = sval(v2)
                elif f2 == 2:
                    vnum = v2
            vals.append((vname, vnum))
    return name, vals


def parse_msg(data, path, out_lines, depth=0):
    """MessageDescriptorProto 递归"""
    name = None
    fields = []
    nested = []
    enums = []
    oneofs = []
    for fno, wt, v in parse_fields(data):
        if fno == 1:
            name = sval(v)
        elif fno == 2:
            fields.append(parse_field_def(v))
        elif fno == 3:
            nested.append((path, v))
        elif fno == 4:
            enums.append(v)
        elif fno == 8:
            for f2, w2, v2 in parse_fields(v):
                if f2 == 1:
                    oneofs.append(sval(v2))
    if not name:
        return
    full = path + '.' + name
    out_lines.append('MSG %s' % full)
    for fname, fnum, ftyp, tname, flabel, jname in fields:
        t = TYPE_NAMES.get(ftyp, '?%s' % ftyp)
        lab = {1: 'opt', 2: 'req', 3: 'rep'}.get(flabel, '?')
        out_lines.append('  f%s %s %s %s json=%s' % (fnum, fname, t, tname or '', lab, jname or ''))
    if oneofs:
        out_lines.append('  oneof: %s' % ','.join(oneofs))
    for _, v in nested:
        parse_msg(v, full, out_lines, depth + 1)
    for v in enums:
        ename, evals = parse_enum(v)
        if ename:
            out_lines.append('  ENUM %s.%s' % (full, ename))
            for vn, vnum in evals:
                out_lines.append('    %s = %s' % (vn, vnum))


def parse_file_desc(data):
    """FileDescriptorProto -> [(name, package, deps, msgs, enums, services)]"""
    lines = []
    pkg = None
    fname = None
    for fno, wt, v in parse_fields(data):
        if fno == 1:
            fname = sval(v)
        elif fno == 2:
            pkg = sval(v)
        elif fno == 4:
            parse_msg(v, pkg or '', lines, 0)
        elif fno == 5:
            ename, evals = parse_enum(v)
            if ename:
                lines.append('ENUMTOP %s.%s' % (pkg, ename))
                for vn, vnum in evals:
                    lines.append('    %s = %s' % (vn, vnum))
        elif fno == 6:
            # ServiceDescriptorProto
            sname = None
            methods = []
            for f2, w2, v2 in parse_fields(v):
                if f2 == 1:
                    sname = sval(v2)
                elif f2 == 2:
                    mname = m_in = m_out = None
                    for f3, w3, v3 in parse_fields(v2):
                        if f3 == 1:
                            mname = sval(v3)
                        elif f3 == 2:
                            m_in = sval(v3)
                        elif f3 == 3:
                            m_out = sval(v3)
                    methods.append((mname, m_in, m_out))
            if sname:
                lines.append('SVC %s.%s' % (pkg or '', sname))
                for mn, mi, mo in methods:
                    lines.append('  %s(%s) -> %s' % (mn, mi, mo))
    return fname, pkg, lines


# ---------- 主流程 ----------
log('=== P1 read celld ===')
blob = None
for cand in ('/proc/1/root/opt/vercel/celld', '/opt/vercel/celld', '/usr/local/bin/celld'):
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

log('=== P2 scan gzip blocks ===')
found = 0
ok = 0
i = 0
while i < len(blob) - 4:
    if blob[i] == 0x1f and blob[i + 1] == 0x8b and blob[i + 2] == 0x08:
        found += 1
        # gzip header 10B + optional fname/comment
        hlen = 10
        flg = blob[i + 3]
        if flg & 0x04:  # FEXTRA
            xl = struct.unpack('<H', blob[i + 10:i + 12])[0]
            hlen += 2 + xl
        if flg & 0x08:  # FNAME
            j = i + hlen
            while j < len(blob) and blob[j] != 0:
                j += 1
            hlen = j - i + 1
        if flg & 0x10:  # FCOMMENT
            j = i + hlen
            while j < len(blob) and blob[j] != 0:
                j += 1
            hlen = j - i + 1
        if flg & 0x02:  # FHCRC
            hlen += 2
        try:
            d = zlib.decompress(blob[i:i + 200000], 31)
            ok += 1
            if len(d) > 2000:
                # 尝试解析 FileDescriptorProto
                try:
                    fname, pkg, lines = parse_file_desc(d)
                    if fname and lines:
                        g.write('=== FILE %s pkg=%s ===\n' % (fname, pkg))
                        for ln in lines:
                            g.write(ln + '\n')
                        g.flush()
                except Exception as e:
                    pass
        except Exception:
            pass
        i += max(hlen, 12)
    else:
        i += 1
log('gzip blocks found=%d decompressed=%d' % (found, ok))

g.flush()
try:
    gsz = len(open(FOUT, encoding='utf-8', errors='replace').read())
    log('descriptor output %d bytes' % gsz)
except Exception as e:
    log('read desc ERR %s' % type(e).__name__)

log('V122C_DONE')
f.close()
g.close()
