#!/usr/bin/env python3
"""
Nuclei 漏洞扫描包装脚本。
用法: python scan.py <目标URL>
"""

import subprocess
import sys
import os
from datetime import datetime

def run_nuclei(target, mode='standard', tech_stack=None):
    """
    Nuclei 漏洞扫描
    
    Args:
        target: 目标 URL
        mode: 扫描模式 ('fast', 'standard', 'full')
        tech_stack: 技术栈信息（可选）
    """
    # 使用固定文件名，每次覆盖
    output_file = "nuclei_scan.txt"
    
    # 直接使用系统 PATH 中的 nuclei 命令
    nuclei_exe = 'nuclei'
    
    # 三种扫描模式配置
    modes = {
        'fast': {
            'concurrency': 25,
            'timeout': 5,
            'rate_limit': 150,
            'retries': 1,
            'severity': 'critical,high',
            'exclude_tags': 'fuzz,headless,network,dns,ssl,file,osint,mobile,app,android,ios,info,low,medium',
            'description': '快速扫描（仅Critical+High，5-10分钟）'
        },
        'standard': {
            'concurrency': 25,
            'timeout': 5,
            'rate_limit': 150,
            'retries': 1,
            'severity': 'critical,high,medium',
            'exclude_tags': 'fuzz,headless,network,dns,ssl,file,osint,mobile,app,android,ios,info,low',
            'description': '标准扫描（Critical+High+Medium，10-15分钟）'
        },
        'full': {
            'concurrency': 20,
            'timeout': 5,
            'rate_limit': 100,
            'retries': 1,
            'severity': 'critical,high,medium,low',
            'exclude_tags': 'fuzz,headless,network,dns,ssl,file,osint,mobile,app,android,ios,info',
            'description': '全面扫描（所有级别，15-25分钟）'
        }
    }
    
    # 获取配置
    if mode not in modes:
        print(f"[WARN] 未知模式 '{mode}'，使用标准模式")
        mode = 'standard'
    
    config = modes[mode]
    
    # 构建基础命令
    command = [
        nuclei_exe, "-u", target, "-o", output_file,
        "-c", str(config['concurrency']),
        "-timeout", str(config['timeout']),
        "-rate-limit", str(config['rate_limit']),
        "-retries", str(config['retries']),
        "-severity", config['severity'],
        "-exclude-tags", config['exclude_tags'],
        "-duc",  # disable-update-check: 禁用自动更新检查，加快速度
        "-stats", "-silent"
    ]
    
    # 如果提供了技术栈信息，只使用相关模板
    if tech_stack and len(tech_stack) > 0:
        # 将技术栈转换为小写并用逗号分隔
        tech_tags = ','.join([tech.lower().replace(' ', '-') for tech in tech_stack])
        command.extend(['-tags', tech_tags])
        print(f"[INFO] 针对性扫描: 仅使用与 {', '.join(tech_stack)} 相关的Web模板")
    
    try:
        print(f"[INFO] 开始 Nuclei 漏洞扫描...")
        print(f"[INFO] 目标: {target}")
        print(f"[INFO] 模式: {config['description']}")
        print(f"[INFO] 配置: 并发={config['concurrency']}, 超时={config['timeout']}s, 速率限制={config['rate_limit']}req/s")
        print(f"[INFO] 严重级别: {config['severity']}")
        print(f"[INFO] 排除标签: {config['exclude_tags']}")
        print(f"[INFO] 输出文件: {output_file}")
        print("=" * 60)
        
        # 直接运行 Nuclei，等待完成（实时显示输出）
        start_time = datetime.now()
        
        # 使用 Popen 实现实时输出
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            # 不使用 text=True 和 encoding，避免编码问题
            # 稍后手动解码
        )
        
        # 实时读取并显示输出
        for line in iter(process.stdout.readline, b''):
            if line:
                try:
                    # 尝试 UTF-8 解码，失败则忽略错误
                    print(line.decode('utf-8', errors='ignore').strip())
                except:
                    pass
        
        process.wait()
        result = subprocess.CompletedProcess(
            command,
            returncode=process.returncode,
            stdout='',
            stderr=''
        )
        
        elapsed_time = (datetime.now() - start_time).total_seconds()
        elapsed_min = int(elapsed_time // 60)
        elapsed_sec = int(elapsed_time % 60)
        
        # 解析输出，统计发现的漏洞
        matched_count = 0
        if result.stdout:
            for line in result.stdout.splitlines():
                if '[critical]' in line.lower() or '[high]' in line.lower() or '[medium]' in line.lower():
                    matched_count += 1
        
        if result.returncode == 0:
            print(f"[OK] 扫描完成！")
            print(f"[INFO] 耗时: {elapsed_min}分{elapsed_sec}秒")
            print(f"[INFO] 发现漏洞: {matched_count} 个")
            print(f"[INFO] 结果已保存到: {output_file}")
            
            # 如果有漏洞，显示简要信息
            if matched_count > 0 and os.path.exists(output_file):
                print(f"\n[INFO] 查看详细信息:")
                print(f"   type {output_file}")
        else:
            print(f"[ERROR] 扫描失败，返回码: {result.returncode}")
            if result.stderr:
                print(f"[ERROR] 错误信息: {result.stderr[:500]}")
            
    except FileNotFoundError:
        print("未找到Nuclei。请确保nuclei.exe在tools/nuclei/目录下。")
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python scan.py <目标URL> [输出目录] [扫描模式]")
        print("")
        print("扫描模式:")
        print("  fast     - 快速扫描（仅Critical+High，5-10分钟）")
        print("  standard - 标准扫描（Critical+High+Medium，10-15分钟）[默认]")
        print("  full     - 全面扫描（所有级别，15-25分钟）")
        print("")
        print("示例:")
        print("  python scan.py http://example.com")
        print("  python scan.py http://example.com ./output fast")
        sys.exit(1)
    
    target = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else '.'
    scan_mode = sys.argv[3] if len(sys.argv) > 3 else 'standard'
    
    # 切换到输出目录，确保文件生成在正确位置
    if output_dir and output_dir != '.':
        os.chdir(output_dir)
    
    run_nuclei(target, mode=scan_mode)
