import json
for ln in open('_run_v156_out.txt', encoding='utf-8'):
    try:
        d = json.loads(ln)
        if 'data' in d:
            txt = d['data'].replace('\n', '\n')
            print(txt)
    except Exception:
        pass
