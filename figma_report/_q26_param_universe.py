# -*- coding: utf-8 -*-
"""q26: 「服务端参数全集 × 从未出现过参数」终盘对账（本地零请求）
S  = 服务端参数全集：从 _js/*.js 提取
     (1) toAPIParameters/toQueryParameters/toBodyParameters(...) 块内 key（高置信）
     (2) url`/api/...` / url:"/api/..." 窗口内的对象 key 与 query 形态（高召回）
C  = 核心出场证据：全部注入测试脚本(_figma_*/_tmp_/_q* py) + 测试落盘(_r*/_w* txt)
E  = 扩展出场证据：+ JS逆向产出(_q*_out.txt / _q json) + 全部分析文档(md)
输出：
  gap_strict = S - C   （没有任何测试动作接触）
  gap_never  = S - C - E（连分析产出里都没出现过 = 真·从未出现）
"""
import sys, io, re, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DIR = r'D:\scan\figma_report'
JS_DIR = os.path.join(DIR, '_js')
EXCLUDE = ('_q21', '_q22', '_q23', '_q24', '_q25', '_q26')

def read(p):
    try: return open(p, encoding='utf-8', errors='ignore').read()
    except Exception: return ''

def camel_to_snake(s):
    return re.sub(r'([A-Z]+)', lambda m: '_' + m.group(1).lower(), s).lstrip('_')

# ---------- 证据源 ----------
core_txt, extra_txt = [], []
for f in os.listdir(DIR):
    if f.startswith(EXCLUDE): continue
    p = os.path.join(DIR, f)
    if os.path.isdir(p): continue
    if f.endswith('.md'):
        extra_txt.append(read(p)); continue
    if f.endswith('.json') and f.startswith('_q'):
        extra_txt.append(read(p)); continue
    if re.match(r'_q\d+_out', f) and f.endswith('.txt'):
        extra_txt.append(read(p)); continue
    if f.endswith('.py') and (f.startswith('_figma_') or f.startswith('_tmp_') or f.startswith('_q')):
        core_txt.append(read(p)); continue
    if f.endswith('.txt') and (f.startswith('_r') or f.startswith('_w')):
        core_txt.append(read(p)); continue

core_all = '\n'.join(core_txt); extra_all = '\n'.join(extra_txt)
print(f'core files={len(core_txt)} chars={len(core_all)} | extra files={len(extra_txt)} chars={len(extra_all)}')

def token_set(txt):
    s = set()
    for tok in re.findall(r'[A-Za-z_][A-Za-z0-9_]{2,40}', txt):
        s.add(tok); s.add(camel_to_snake(tok)); s.add(tok.lower())
    return s

tok_core, tok_extra = token_set(core_all), token_set(extra_all)
print(f'tokens core={len(tok_core)} extra={len(tok_extra)}')

# ---------- S: 服务端参数全集 ----------
js_files = [f for f in os.listdir(JS_DIR) if f.endswith('.js')]
S = {}
print(f'js files: {len(js_files)}')

CALL = re.compile(r'to(?:API|Query|Body)Parameters\(\s*\{')
for jf in js_files:
    js = read(os.path.join(JS_DIR, jf))
    if not js: continue
    # (1) toAPIParameters 块（配平提取）
    for m in CALL.finditer(js):
        start = m.end() - 1; i = start; depth = 0; ln = len(js)
        while i < ln:
            c = js[i]
            if c in '"\'':
                q = c; i += 1
                while i < ln and js[i] != q:
                    if js[i] == '\\': i += 1
                    i += 1
            elif c == '{': depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0: break
            i += 1
        block = js[start:i+1]
        for km in re.finditer(r'[,{]\s*([a-zA-Z_][a-zA-Z0-9_]{2,40})\s*:', block):
            k = km.group(1); S.setdefault(k, set()).add('toAPI:' + jf)
    # (2) URL 窗口法
    for m in re.finditer(r'url[`"\'](/api/[^`"\']{2,120})[`"\']', js):
        win = js[m.end():m.end()+700]
        for km in re.finditer(r'[,{]\s*([a-zA-Z_][a-zA-Z0-9_]{2,40})\s*:', win):
            k = km.group(1); S.setdefault(k, set()).add('win:' + jf)
        for km in re.finditer(r'[&?]([a-z][a-z0-9_]{2,40})=', win):
            k = km.group(1); S.setdefault(k, set()).add('winq:' + jf)

print(f'S raw = {len(S)}')

# ---------- 过滤噪声 ----------
NOISE = {
 'loadingkey','fallbackerror','promise','dispatch','onsuccess','onfailure','onretry','onerror',
 'onsubmit','onfinish','ondismiss','onclose','onchange','onclick','oncancel','onconfirm','onshow',
 'onhide','ref','store','reduxstore','isloading','isnewquery','newquery','requestpromise',
 'responsetype','responsedata','responsestatus','forwardtodatadog','reportassentryerror',
 'timeoutoverride','retrycount','sharefilelabel','submitbuttontext','showtitle','modaltitle',
 'headertext','secondarytext','placeholder','characterlimit','displaytext','errormsg','errormessage',
 'errormessage','fallbackerror','successmessage','loadingelementid','showuploaderror','showuploading',
 'showsuccess','disclaimer','recordingkey','entrypoint','usertriggered','optimistid','optimisticid',
 'storeinrecentskey','canretry','shouldredirectoncreate','onfoldercreated','oncloseorcomplete',
 'startproupgradeflow','showbreadcrumbs','localstorage','onceloaded','shouldshow','onstatechange',
}
EVENT_SUFFIX = ('_started','_failed','_completed','_clicked','_viewed','_shown','_dismissed',
                '_rendered','_requested','_loaded','_opened','_closed','_entered','_cancelled',
                '_changed','_impression','_shown','_seen','_initiated','_selected','_scroll',
                '_pressed','_toggled','_submitted','_updated','_created','_deleted','_inserted')

def keep(k):
    if len(k) < 3 or len(k) > 40: return False
    if re.match(r'^[a-z]{1,2}\d?$', k): return False
    if re.match(r'^[a-zA-Z]_[a-zA-Z0-9]{1,2}$', k): return False
    if re.match(r'^[A-Z0-9_]+$', k): return False
    if k.lower() in NOISE: return False
    ks = camel_to_snake(k)
    if any(ks.endswith(sfx) or k.endswith(sfx) for sfx in EVENT_SUFFIX): return False
    return True

S2 = {k: v for k, v in S.items() if keep(k)}

def variants(k):
    return {k, camel_to_snake(k), k.lower(), camel_to_snake(k).lower()}

def seen(k, toks):
    return any(v in toks for v in variants(k))

gap_strict = sorted(k for k in S2 if not seen(k, tok_core))
gap_never  = sorted(k for k in gap_strict if not seen(k, tok_extra))

print(f'S filtered = {len(S2)}')
print(f'gap_strict (no test touch)   = {len(gap_strict)}')
print(f'gap_never  (never anywhere)  = {len(gap_never)}')
print()
print('===== gap_never 全量 =====')
for k in gap_never:
    print('  ', k)

save = {
 'S_filtered': sorted(S2.keys()),
 'gap_strict': gap_strict,
 'gap_never': gap_never,
 'evidence_counts': {'core_chars': len(core_all), 'extra_chars': len(extra_all)},
}
with open(os.path.join(DIR, '_q26_gap_result.json'), 'w', encoding='utf-8') as fh:
    json.dump(save, fh, ensure_ascii=False, indent=1)
print('\nsaved: _q26_gap_result.json')
