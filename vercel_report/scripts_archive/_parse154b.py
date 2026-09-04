import json
for ln in open('_run_v154_out.txt', encoding='utf-8'):
    try:
        d = json.loads(ln)
        if 'data' in d:
            txt = d['data'].replace('\n', '\n')
            keep = False
            for line in txt.split('\n'):
                if ('Create drive_id' in line or 'SUCCESS' in line or 'V154_DONE' in line
                        or '=== 3' in line or '=== 4' in line or 'heap scan done' in line
                        or 'PTRACE_ATTACH' in line or 'COW v154c' in line):
                    keep = True
            if keep:
                print('===== BLOCK =====')
                print(txt[:9000])
    except Exception as e:
        pass
