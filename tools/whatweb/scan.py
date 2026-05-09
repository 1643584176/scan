#!/usr/bin/env python3
"""
Wappalyzer 技术栈检测包装脚本。
用法: python scan.py <目标URL>
"""

import json
from datetime import datetime
from Wappalyzer import Wappalyzer, WebPage

def run_wappalyzer(target):
    output_file = f"wappalyzer_scan_{target.replace('http://', '').replace('https://', '').replace('/', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        wappalyzer = Wappalyzer.latest()
        webpage = WebPage.new_from_url(target)
        techs = wappalyzer.analyze(webpage)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(techs, f, indent=4)
        print(f"技术栈数据已保存到 {output_file}")
        print("检测到的技术:", list(techs.keys()))
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("用法: python scan.py <目标URL>")
        sys.exit(1)
    target = sys.argv[1]
    run_wappalyzer(target)
