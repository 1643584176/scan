# -*- coding: utf-8 -*-
# r221pre-2: notification_type 枚举全集 / hexHash 来源 / audios 族 / manifest 调用点
import sys, io, os, re, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

js_dir = '_js'
files = glob.glob(os.path.join(js_dir, '*.js')) + glob.glob(os.path.join(js_dir, '**', '*.js'), recursive=True)
files = list(dict.fromkeys(files))
print(f'JS 文件: {len(files)} 个')

def scan(name, pattern, maxhit=30, ctx=160):
    print(f'\n### {name} —— /{pattern}/')
    hit = 0
    rx = re.compile(pattern)
    for f in files:
        try:
            txt = open(f, encoding='utf-8', errors='replace').read()
        except Exception:
            continue
        for m in rx.finditer(txt):
            s = max(0, m.start() - ctx); e = min(len(txt), m.end() + ctx)
            seg = txt[s:e].replace('\n', ' ')
            print(f'  {os.path.basename(f)}: …{seg}…')
            hit += 1
            if hit >= maxhit:
                print('  (截断)')
                return
    if hit == 0:
        print('  (无命中)')

scan('notification 枚举全集(_NOTIFICATION=)', r'[A-Z_]+_NOTIFICATION\s*=\s*"', maxhit=30)
scan('by 对象枚举上下文', r'by\s*[=:]\s*\(?\(?\w+\|\|', maxhit=10)
scan('hexHash/hex_hash 全出现', r'hexHash|hex_hash', maxhit=25)
scan('audios 端点串', r'/audios[^"\'\s\\]{0,60}', maxhit=20)
scan('audios JS 方法名', r'getAudios|createAudiosUpload|AudiosSchema', maxhit=15)
scan('files 域 manifest 字符串', r'files/\$\{[^}]*\}/videos/\$\{[^}]*\}/manifest', maxhit=10)
scan('plugin/widget videos manifest', r'plugins/\$\{[^}]*\}/videos|widgets/\$\{[^}]*\}/videos', maxhit=10)
