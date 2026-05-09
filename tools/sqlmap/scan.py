#!/usr/bin/env python3
"""
SQLMap SQL注入测试包装脚本。
用法: python scan.py <目标URL>
"""

import subprocess
import sys
import os
from datetime import datetime

def run_sqlmap(target):
    output_dir = f"sqlmap_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    command = ["sqlmap", "-u", target, "--batch", "--output-dir", output_dir]
    try:
        print(f"正在运行: {' '.join(command)}")
        result = subprocess.run(command, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("错误:", result.stderr)
        print(f"输出已保存到 {output_dir}")
    except FileNotFoundError:
        print("未找到SQLMap。请安装SQLMap。")
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python scan.py <目标URL>")
        sys.exit(1)
    target = sys.argv[1]
    run_sqlmap(target)
