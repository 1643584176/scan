# -*- coding: utf-8 -*-
# q49: 终局边角核查 —— 结构层最后角度是否真没打过（全库 340+ 脚本）
import sys, io, os, re, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

files = glob.glob('_*.py')
print(f'脚本总数: {len(files)}')

def scan(name, pattern, maxhit=12, ctx=110):
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
            print(f'  {f}: …{txt[s:e].replace(chr(10), " ")}…')
            hit += 1
            if hit >= maxhit:
                print('  (截断)'); return
    if hit == 0:
        print('  (无命中=未打过)')

scan('双重编码 %2527/%2525 痕迹', r'%2527|%25252|%2525')
scan('排序参数 sort/order/order_by', r'text=.*thumbnails.*sort|sort=|order_by=|order=asc|order=desc')
scan('头部注入 XFF/X-Real/X-Orig', r'X-Forwarded|X-Real-IP|X-Original')
scan('Content-Type 分流 text/plain/multipart', r"Content-Type.*text/plain|multipart/form-data")
scan('notif 路径尾斜杠/双斜杠/点段', r'notification_settings/|//api/billing|/\./notification')
scan('键名畸形 __proto__/constructor', r'__proto__|constructor.*body|prototype')
scan('加号语义 plan_id=+', r"plan_id=.*['\"]\+|%2[Bb]|query.*\+")
scan('realtime_token 历史', r'realtime_token|RealtimeToken')
scan('不是团队 plan_type/invite/nested 边角', r'plan_type=organization|org_id=|include_deleted|include_debug')
scan('Accept 内容协商', r"Accept.*text/html|Accept.*application/xml")
