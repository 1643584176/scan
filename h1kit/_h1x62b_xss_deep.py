# -*- coding: utf-8 -*-
"""XSS 链深挖:filterXSS 配置 + marked 渲染器 + dangerouslySetInnerHTML(2026-09-08)"""
import re

with open(r"D:\scan\h1kit\_h1x4_app.js", "r", encoding="utf-8", errors="replace") as f:
    data = f.read()

# 1. xss 库引用上下文
print("=== 'xss' 引用上下文")
for m in list(re.finditer(r"filterXSS|xss\s*[=,.]|require\(['\"]xss|from ['\"]xss", data))[:10]:
    ctx = data[max(0, m.start() - 150):m.start() + 400]
    print("  ...", ctx[:500].replace("\n", " "))
    print()

# 2. marked 配置(renderer/breaks/自定义)
print("=== marked 配置上下文")
for m in list(re.finditer(r"marked\.(use|setOptions|Renderer|parse|Parser)|new\s+marked|Marked\(|renderer\s*[:=]", data))[:12]:
    ctx = data[max(0, m.start() - 200):m.start() + 500]
    print("  ...", ctx[:650].replace("\n", " "))
    print()

# 3. dangerouslySetInnerHTML 上下文(渲染点)
print("=== dangerouslySetInnerHTML 数量与上下文")
hits = list(re.finditer(r"dangerouslySetInnerHTML", data))
print("count:", len(hits))
for m in hits[:15]:
    ctx = data[max(0, m.start() - 250):m.start() + 250]
    print("  ...", ctx[:450].replace("\n", " "))
    print()
