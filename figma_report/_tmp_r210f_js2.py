# -*- coding: utf-8 -*-
# r210f: JS url 模板全量提取 —— workshop 族/兄弟端点复查 + viewHash
import io, re
d = 'D:/scan/figma_report/_js'
js = io.open(d + '/figma_app-main.js', encoding='utf-8', errors='replace').read()
print('js size =', len(js))

print()
print('===== 1. url` 模板过滤: workshop / mark_diagram / claim / hub / try =====')
tpls = set(re.findall(r'url`([^`]+)`', js))
print('total url templates =', len(tpls))
for t in sorted(tpls):
    low = t.lower()
    if any(k in low for k in ('workshop', 'mark_diagram', 'claim', 'hub', 'try_file', 'tryfile')):
        print('  TPL', t)

print()
print('===== 2. "workshop" 文本上下文（含非模板）=====')
for m in list(re.finditer(r'workshop', js, re.I))[:12]:
    i = m.start()
    seg = js[max(0, i - 110):i + 130].replace('\n', ' ')
    print('  >>>', seg)
    print('  ---')

print()
print('===== 3. mark_diagram / markDiagram 全部命中 =====')
for m in list(re.finditer(r'mark_diagram|markDiagram|markInserted|diagram_insert', js))[:20]:
    i = m.start()
    seg = js[max(0, i - 130):i + 170].replace('\n', ' ')
    print('  >>>', seg)
    print('  ---')

print()
print('===== 4. viewHash: ListCollectionsView / ListFieldSchemasView / HasCollectionsView =====')
for nm in ('ListCollectionsView', 'ListFieldSchemasView', 'ListItemsView', 'HasCollectionsView'):
    m = re.search(r'o\("' + nm + r'",\[([^\]]*)\],"([0-9a-f]{16,})"\)', js)
    if m:
        print(f'  {nm} hash={m.group(2)}')
    else:
        print(f'  {nm} NOT FOUND(主包)')

print()
print('===== 5. claimTryFile 兄弟（同对象成员）=====')
i = js.find('claimTryFile')
if i > 0:
    seg = js[max(0, i - 400):i + 900]
    print(seg.replace('\n', ' ')[:1400])
print('DONE210f')
