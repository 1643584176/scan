#!/usr/bin/env python3
"""
Subfinder 子域名扫描模块（独立模块，完全解耦）
可以单独运行: python modules/subdomain_scan.py <domain> <output_dir>
"""
import sys
import os
import subprocess
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.utils import log, ensure_dir

def scan_subdomains(domain, output_dir='.'):
    """
    使用 Subfinder 扫描子域名
    
    Args:
        domain: 目标域名（例如：example.com）
        output_dir: 输出目录
    
    Returns:
        list: 发现的子域名列表
    """
    ensure_dir(output_dir)
    
    log(f"开始子域名扫描: {domain}")
    log("这个过程可能需要2-5分钟，请耐心等待...")
    
    output_file = os.path.join(output_dir, 'subdomains.txt')
    
    try:
        # 直接使用系统 PATH 中的 subfinder 命令
        subfinder_exe = 'subfinder'
        
        # 构建命令
        cmd = [
            subfinder_exe,
            '-d', domain,
            '-o', output_file,
            '-silent',
            '-nW',           # 移除不活跃的域名
            '-max-time', '300'  # 最大运行时间 5 分钟
        ]
        
        log(f"执行命令: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=600  # 10分钟超时
        )
        
        if result.returncode == 0 and os.path.exists(output_file):
            # 读取子域名列表
            with open(output_file, 'r', encoding='utf-8') as f:
                subdomains = [line.strip() for line in f if line.strip()]
            
            log(f"[✓] 子域名扫描完成，发现 {len(subdomains)} 个子域名")
            
            # 保存统计信息
            stats_file = os.path.join(output_dir, 'subdomain_stats.json')
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'domain': domain,
                    'total_subdomains': len(subdomains),
                    'subdomains': subdomains
                }, f, indent=2, ensure_ascii=False)
            
            log(f"结果已保存到: {output_file}")
            return subdomains
        else:
            log(f"[!] Subfinder 返回码 {result.returncode}")
            if result.stderr:
                log(f"错误信息: {result.stderr.decode('utf-8', errors='ignore')}")
            return []
            
    except FileNotFoundError:
        log("[✗] 未找到 subfinder 命令")
        log("安装方法: go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest")
        return []
    except subprocess.TimeoutExpired:
        log("[✗] 子域名扫描超时（10分钟）")
        # 尝试读取已生成的文件
        if os.path.exists(output_file):
            with open(output_file, 'r', encoding='utf-8') as f:
                subdomains = [line.strip() for line in f if line.strip()]
            log(f"使用已扫描的 {len(subdomains)} 个子域名")
            return subdomains
        return []
    except Exception as e:
        log(f"[✗] 子域名扫描异常: {e}")
        import traceback
        log(traceback.format_exc())
        return []

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python modules/subdomain_scan.py <domain> [output_dir]")
        print("\n示例:")
        print("  python modules/subdomain_scan.py example.com ./output")
        sys.exit(1)
    
    domain = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else '.'
    
    subdomains = scan_subdomains(domain, output_dir)
    
    if subdomains:
        print(f"\n发现的子域名 ({len(subdomains)} 个):")
        for sd in subdomains[:20]:  # 只显示前20个
            print(f"  - {sd}")
        if len(subdomains) > 20:
            print(f"  ... 还有 {len(subdomains) - 20} 个")
    else:
        print("\n未发现子域名")
