#!/usr/bin/env python3
"""
使用 Nuclei 扫描 SG 站点的所有接口
"""

import subprocess
import os
from datetime import datetime

def run_nuclei_scan():
    """执行 Nuclei 扫描"""
    
    # 配置参数
    input_file = 'js/sg_urls_final.txt'  # 使用清理后的 SG URL 文件
    output_dir = 'nuclei_sg_scan'
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    print("=" * 80)
    print("Nuclei SG 站点扫描")
    print("=" * 80)
    print(f"输入文件: {input_file}")
    print(f"输出目录: {output_dir}")
    print(f"时间戳: {timestamp}")
    print()
    
    # 检查输入文件
    if not os.path.exists(input_file):
        print(f"❌ 错误: 找不到输入文件 {input_file}")
        return
    
    with open(input_file, 'r', encoding='utf-8-sig', errors='ignore') as f:
        # 过滤掉空行和无效行，只保留以 http 开头的 URL
        urls = [line.strip() for line in f if line.strip() and line.strip().startswith('http')]
    
    print(f"📋 找到 {len(urls)} 个 URL")
    print()
    
    # Nuclei 扫描配置
    nuclei_cmd = [
        'nuclei',
        '-l', input_file,  # 从文件读取目标
        '-o', f'{output_dir}/results_{timestamp}.txt',  # 输出结果
        '-jsonl', f'{output_dir}/results_{timestamp}.jsonl',  # JSON 格式输出
        '-severity', 'critical,high,medium,low,info',  # 所有级别
        '-c', '25',  # 并发数
        '-timeout', '8',  # 超时 8 秒
        '-rate-limit', '150',  # 速率限制 150 req/s
        '-retries', '1',  # 重试次数
        '-bulk-size', '25',  # 批量大小
        '-no-color',  # 禁用颜色（便于日志记录）
        '-stats',  # 显示统计信息
        '-si', '30',  # 每 30 秒显示一次统计
    ]
    
    print("🚀 开始 Nuclei 扫描...")
    print(f"命令: {' '.join(nuclei_cmd)}")
    print()
    
    try:
        # 执行 Nuclei 扫描
        result = subprocess.run(
            nuclei_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        
        # 保存完整日志
        log_file = f'{output_dir}/scan_log_{timestamp}.txt'
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(result.stdout)
        
        print()
        print("=" * 80)
        print("扫描完成!")
        print("=" * 80)
        print(f"✅ 结果文件: {output_dir}/results_{timestamp}.txt")
        print(f"✅ JSON 结果: {output_dir}/results_{timestamp}.jsonl")
        print(f"✅ 完整日志: {log_file}")
        print()
        
        # 统计结果
        if result.stdout:
            lines = result.stdout.strip().split('\n')
            
            # 查找漏洞统计
            vuln_count = 0
            for line in lines:
                if '[' in line and ']' in line and any(sev in line.lower() for sev in ['critical', 'high', 'medium', 'low', 'info']):
                    vuln_count += 1
            
            print(f"📊 发现的漏洞/问题数量: {vuln_count}")
            
            # 显示前 20 个结果
            if vuln_count > 0:
                print("\n🔍 前 20 个发现:")
                print("-" * 80)
                shown = 0
                for line in lines:
                    if '[' in line and ']' in line and any(sev in line.lower() for sev in ['critical', 'high', 'medium', 'low', 'info']):
                        print(line)
                        shown += 1
                        if shown >= 20:
                            break
        
        print()
        print("💡 提示:")
        print(f"   - 查看完整结果: cat {output_dir}/results_{timestamp}.txt")
        print(f"   - 查看 JSON 结果: cat {output_dir}/results_{timestamp}.jsonl | jq")
        print(f"   - 查看日志: cat {log_file}")
        
    except FileNotFoundError:
        print("❌ 错误: 找不到 nuclei 命令")
        print("   请确保 Nuclei 已安装并添加到 PATH")
        print("   安装方法: go install -v github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest")
    
    except Exception as e:
        print(f"❌ 扫描失败: {str(e)}")

if __name__ == '__main__':
    run_nuclei_scan()
