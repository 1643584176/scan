#!/usr/bin/env python3
"""
Nmap 网络扫描包装脚本。
用法: python scan.py <目标>
"""

import subprocess
import sys
import os
from datetime import datetime

def run_nmap(target):
    output_file = f"nmap_scan_{target.replace('/', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    command = ["nmap", "-sV", "-O", target, "-oN", output_file]
    try:
        print(f"正在运行: {' '.join(command)}")
        result = subprocess.run(command, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("错误:", result.stderr)
        print(f"输出已保存到 {output_file}")
    except FileNotFoundError:
        print("未找到Nmap。请安装Nmap。")
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python scan.py <目标>")
        sys.exit(1)
    target = sys.argv[1]
    run_nmap(target)
