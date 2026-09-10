# -*- coding: utf-8 -*-
import io, re
js = io.open('_js/figma_app-main.js', encoding='utf-8', errors='replace').read()
print('== __requestId ctx')
hits = list(re.finditer(r'.{100}__requestId.{140}', js))
print('total', len(hits))
for m in hits[:14]:
    print('RQ>', repr(m.group(0))[:250])
print('== requestId field usage')
for m in list(re.finditer(r'.{80}"requestId".{120}', js))[:10]:
    print('RI>', repr(m.group(0))[:220])
print('== sinatra / static query ctx')
for m in list(re.finditer(r'.{80}sinatra.{120}', js))[:6]:
    print('SN>', repr(m.group(0))[:220])
for m in list(re.finditer(r'.{80}Static quer.{120}', js))[:4]:
    print('SQ>', repr(m.group(0))[:220])
print('DONE')
