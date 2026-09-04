import json
n = 0
ok = 0
for ln in open('_run_v154_out.txt', encoding='utf-8'):
    n += 1
    try:
        d = json.loads(ln)
        ok += 1
        if 'data' in d and 'COW' in d['data']:
            txt = d['data'].replace('\n', '\n')
            print('LINE %d OK, data len=%d' % (n, len(d['data'])))
            # 打印阶段 3 附近
            idx = txt.find('=== 3')
            print(repr(txt[max(0,idx-100):idx+2000]) if idx >= 0 else 'NO ===3 marker')
            break
    except Exception as e:
        print('LINE %d FAIL %s' % (n, type(e).__name__))
print('total=%d ok=%d' % (n, ok))
