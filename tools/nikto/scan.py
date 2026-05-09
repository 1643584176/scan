#!/usr/bin/env python3
"""
Nuclei 漏洞扫描包装脚本。
用法: python scan.py <目标URL>
"""

import subprocess
import sys
import os
from datetime import datetime

def run_nuclei(target):
    output_file = f"nuclei_scan_{target.replace('http://', '').replace('https://', '').replace('/', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    nuclei_exe = os.path.join(os.path.dirname(__file__), '..', 'nuclei', 'nuclei.exe')
    # 添加并发和超时以加快扫描
    command = [nuclei_exe, "-u", target, "-o", output_file, "-c", "5", "-timeout", "10"]
    try:
        print(f"正在运行: {' '.join(command)}")
        result = subprocess.run(command, capture_output=True, text=True)
        print(f"输出已保存到 {output_file}")
        if result.stderr:
            print("错误:", result.stderr)
    except FileNotFoundError:
        print("未找到Nuclei。请确保nuclei.exe在tools/nuclei/目录下。")
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python scan.py <目标URL>")
        sys.exit(1)
    target = sys.argv[1]
    run_nuclei(target)
