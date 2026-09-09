# -*- coding: utf-8 -*-
"""XSS 链考古:sanitize 库与配置(bundle)(2026-09-08)"""
import re

with open(r"D:\scan\h1kit\_h1x4_app.js", "r", encoding="utf-8", errors="replace") as f:
    data = f.read()

# 1. sanitize 库名
print("=== 库名命中")
for kw in ["DOMPurify", "dompurify", "sanitizeHtml", "sanitize-html", "marked", "markdown-it", "remarkable",
           "allowlist", "ALLOWED_TAGS", "ALLOWED_ATTR", "ADD_ATTR", "FORBID_TAGS", "prosemirror", "tiptap",
           "xss", "escapeHtml", "htmlspecialchars", "AutoSanitize", "cleanHtml"]:
    c = data.lower().count(kw.lower())
    if c:
        print(f"  {kw}: {c}")

# 2. markdown 渲染上下文(找渲染库调用)
print("\n=== markdown 渲染附近 600 字符")
for m in list(re.finditer(r"(markdown|renderMarkdown|markdownIt|MarkdownIt|marked\.)", data))[:8]:
    ctx = data[max(0, m.start() - 200):m.start() + 600]
    # 只打含 html/link/target 的片段(配置)
    if re.search(r"(html|link|sanitize|breaks|typographer)", ctx, re.I):
        print("  ...", ctx[:700].replace("\n", " ")[:600])
        print()

# 3. 报告正文渲染组件附近(找渲染时的净化开关)
print("=== vulnerability_information 渲染上下文")
for m in list(re.finditer(r"vulnerability_information", data))[:3]:
    ctx = data[max(0, m.start() - 300):m.start() + 300]
    print("  ...", ctx[:500].replace("\n", " "))
    print()
