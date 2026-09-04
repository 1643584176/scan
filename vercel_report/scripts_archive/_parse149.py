import json
for ln in open('_run_v149_out.txt', encoding='utf-8'):
    try:
        d = json.loads(ln)
        if 'data' in d:
            print(d['data'].replace('\n', '\n'))
    except Exception:
        pass
