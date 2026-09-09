# -*- coding: utf-8 -*-
"""T4 考古:上传流程(bundle 内 upload 端点/multipart/文件名处理)(2026-09-08)"""
import re

with open(r"D:\scan\h1kit\_h1x4_app.js", "r", encoding="utf-8", errors="replace") as f:
    data = f.read()

# 1. upload URL 形态
print("=== URL 形态")
for pat in [r'["\'](/[a-z0-9_\-/]*(?:upload|attachment|file|asset|media)[a-z0-9_\-/]*)["\']',
            r'["\'](https?://[^"\']*(?:upload|attachment|file)[^"\']*)["\']']:
    hits = sorted(set(re.findall(pat, data, re.I)))
    for h in hits[:30]:
        print("  ", h)

# 2. UploadReportIntentAttachmentsInput / UploadAttachmentInput 结构上下文(文档串)
print("\n=== UploadAttachment 文档串")
for m in re.finditer(r"(mutation|UploadAttachment|UploadReportIntentAttachments|uploadAttachment)", data):
    ctx = data[m.start():m.start() + 900]
    if "Upload" in ctx[:200] or "upload" in ctx[:200]:
        snippet = ctx[:700].replace("\n", " ")
        if "upload" in snippet.lower():
            print("  ...", snippet[:500])
            print()
