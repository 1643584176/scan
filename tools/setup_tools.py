#!/usr/bin/env python3
"""
设置扫描工具的脚本。
检查所需的工具是否已安装，并提供安装说明。
"""

import subprocess
import sys
import os

def check_tool(tool_name, command):
    try:
        if tool_name == "Nuclei":
            command = os.path.join(os.getcwd(), 'tools', 'nuclei', 'nuclei.exe') + " -version"
        result = subprocess.run(command, capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            print(f"✓ {tool_name} 已安装。")
            return True
        else:
            print(f"✗ {tool_name} 未安装或不在PATH中。")
            return False
    except Exception as e:
        print(f"检查 {tool_name} 时出错: {e}")
        return False

def main():
    tools = [
        ("Nmap", "nmap --version"),
        ("SQLMap", "sqlmap --version"),
        ("Wappalyzer", "python -c 'from Wappalyzer import Wappalyzer; print(Wappalyzer.latest())'"),
        ("Nuclei", "tools\\nuclei\\nuclei.exe -version"),
    ]

    print("正在检查扫描工具安装情况...\n")

    all_installed = True
    for name, cmd in tools:
        if not check_tool(name, cmd):
            all_installed = False

    if not all_installed:
        print("\n缺少某些工具。请安装它们：")
        print("- Nmap: 从 https://nmap.org/download.html 下载")
        print("- SQLMap: pip install sqlmap 或从 https://sqlmap.org/ 下载")
        print("- Wappalyzer: pip install Wappalyzer")
        print("\n对于Windows，考虑使用WSL来运行Linux工具。")
    else:
        print("\n所有工具都已安装！")

if __name__ == "__main__":
    main()
