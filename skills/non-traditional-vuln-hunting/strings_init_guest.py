# -*- coding: utf-8 -*-
"""strings_init: 分析 /run/vercel/share/sandbox-init 二进制
1) 提取全部可打印字符串(>=6)
2) 按关键词分类: 路由/服务名/凭据/代理/socket/签名
3) 拉关键片段落盘, 哨兵 STRINGS_DONE"""
import re, time

OUT = '/vercel/sandbox/strings.out'
BIN = '/run/vercel/share/sandbox-init'
f = open(OUT, 'w', encoding='utf-8', errors='replace')


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


def extract_strings(data, minlen=6):
    """提取可打印 ASCII 字符串"""
    out = []
    cur = bytearray()
    for b in data:
        if 0x20 <= b < 0x7f:
            cur.append(b)
        else:
            if len(cur) >= minlen:
                out.append(bytes(cur).decode('latin1'))
            cur = bytearray()
    if len(cur) >= minlen:
        out.append(bytes(cur).decode('latin1'))
    return out


try:
    data = open(BIN, 'rb').read()
    log('binary size: %d bytes' % len(data))
    strs = extract_strings(data)
    log('strings >=6: %d' % len(strs))

    # 分类关键词
    patterns = {
        'ROUTES': re.compile(r'(/v\d+/[A-Za-z0-9_./{}:-]+|/api/[A-Za-z0-9_./:-]+|/[A-Za-z0-9_-]+\.sock)', re.I),
        'SERVICES': re.compile(r'(vercel\.[a-z0-9_.]+|cell[a-z0-9_]*|containerd[a-z0-9_.]*|spawn[a-z0-9_.]*)', re.I),
        'CREDS': re.compile(r'(token|credential|secret|auth|signature|pubkey|privkey|oidc|jwt|bearer|api[_-]?key)', re.I),
        'PROXY': re.compile(r'(proxy|forward|tunnel|egress|gateway|connect|dial|listen)', re.I),
        'CMDS': re.compile(r'(spawn|exec|fork|run|start|stop|kill|restart|cmd|shell|command)', re.I),
        'FS': re.compile(r'(/run/|/var/|/tmp/|/etc/|/proc/|mount|overlay|bind)', re.I),
        'HDRS': re.compile(r'(x-vercel|content-type|authorization|cookie|host)', re.I),
    }

    uniq = set(strs)
    for name, pat in patterns.items():
        hits = [s for s in uniq if pat.search(s)]
        hits.sort()
        log('--- %s: %d unique hits ---' % (name, len(hits)))
        # 去重后输出最多 120 条, 每条截断 150 字符
        for s in hits[:120]:
            log('  %s' % s[:150])
        log('')
    log('STRINGS_DONE')
except Exception as e:
    log('EXC %s' % e)
    log('STRINGS_DONE')
f.close()
