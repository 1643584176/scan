# -*- coding: utf-8 -*-
"""挖 JS 3: J 所在模块头部(N=r()) + C2 定义定位 + 版本历史 UI 上下文"""
import io

F = r'D:\scan\figma_report\_js\figma_app-main.js'
t = io.open(F, encoding='utf-8', errors='ignore').read()

print('===== 1) N.C2 全部引用 =====')
i = 0
while True:
    i = t.find('N.C2', i)
    if i < 0:
        break
    print('pos', i, '::', t[i - 200:i + 100].replace('\n', ' '))
    print()
    i += 4

print('===== 2) J 模块头 / N 绑定 =====')
anchor = 2587384
head = t.rfind('r.d(t,{', 0, anchor)
print('module head pos', head)
print(t[head:head + 260].replace('\n', ' '))
print()
j = t.find('N=r(', head)
lim = anchor + 300
cnt = 0
while j >= 0 and j < lim and cnt < 30:
    print('N=r( @', j, ':', t[j - 60:j + 140].replace('\n', ' '))
    j = t.find('N=r(', j + 1)
    cnt += 1
print()
print('===== 3) N=( 变体 =====')
j = t.find('N=(', head)
cnt = 0
while j >= 0 and j < lim and cnt < 20:
    print('N=( @', j, ':', t[j - 60:j + 160].replace('\n', ' '))
    j = t.find('N=(', j + 1)
    cnt += 1

print()
print('===== 4) J 函数完整上下文(前 1600) =====')
print(t[anchor - 1600:anchor + 120].replace('\n', ' '))

print()
print('===== 5) 模块 660929 内 C2:()=>eo 的 eo 定义 =====')
m660 = t.find('660929(e,t,r)')
print('m660 pos', m660)
k = t.find('C2:()=>eo', m660)
print('C2->eo at', k)
z = t.find('eo=', m660)
cnt = 0
while z >= 0 and z < m660 + 40000 and cnt < 6:
    print('eo= @', z, ':', t[z - 80:z + 220].replace('\n', ' '))
    z = t.find('eo=', z + 1)
    cnt += 1
print('DONE3')
