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
        
        # 转换 set 类型为 list，以便 JSON 序列化
        def convert_sets(obj):
            if isinstance(obj, set):
                return list(obj)
            elif isinstance(obj, dict):
                return {k: convert_sets(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_sets(i) for i in obj]
            return obj
        
        techs_converted = convert_sets(techs)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(techs_converted, f, indent=4)
        print(f"技术栈数据已保存到 {output_file}")
        # 兼容 dict 和 list 两种格式
        if isinstance(techs_converted, dict):
            print("检测到的技术:", list(techs_converted.keys()))
        elif isinstance(techs_converted, list):
            print("检测到的技术:", techs_converted)
        else:
            print("检测到的技术: []")
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("用法: python scan.py <目标URL>")
        sys.exit(1)
    target = sys.argv[1]
    run_wappalyzer(target)
