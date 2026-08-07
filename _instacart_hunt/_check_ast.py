"""检查 chunk 里 AST 的完整结构（是否有 selectionSet）"""
import re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

src = open('js/3382-d1d7b0ab64135d85-v3.webpack_chunk.js', encoding='utf-8', errors='replace').read()
# 找第一个 Document AST，输出完整 6000 字符
m = re.search(r'\{kind:"Document",definitions:\[', src)
if m:
    i = m.start()
    print(src[i:i+6000])
