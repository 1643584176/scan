# -*- coding: utf-8 -*-
"""检查 index 内容 + OCR 工具检测"""
import sys

txt = open(r'D:\scan\netlify_report\endpoint-map-index.html', encoding='utf-8', errors='ignore').read()
print('index content:', repr(txt))

# 检测 OCR 工具
try:
    import pytesseract
    print('pytesseract: OK')
except ImportError:
    print('pytesseract: missing')

import shutil
print('tesseract cmd:', shutil.which('tesseract'))

# 尝试 PIL 读 PNG 尺寸
try:
    from PIL import Image
    im = Image.open(r'D:\scan\netlify_report\endpoint-map.png')
    print('png size:', im.size)
except ImportError:
    print('PIL: missing')
