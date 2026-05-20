#!/usr/bin/env python3
"""
SQLMap 注入测试模块
可以单独运行: python modules/sqlmap_test.py <urls_file> <output_dir>
"""
import sys
import os
import subprocess
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import get_tool_path, TIMEOUT_SQLMAP
from core.utils import log, read_urls_from_file

def test_sql_injection(urls_file, output_dir='.'):
    """
    使用 SQLMap 测试 SQL 注入
    
    Args:
        urls_file: SQLMap 目标文件路径
        output_dir: 输出目录
    
    Returns:
        list: 测试结果列表
    """
    if not os.path.exists(urls_file):
        log(f"SQLMap 目标文件不存在: {urls_file}")
        return []
    
    # 读取待测试 URL
    sqlmap_urls = read_urls_from_file(urls_file)
    if not sqlmap_urls:
        log("没有待测试的 URL")
        return []
    
    log(f"开始 SQLMap 注入测试（快速模式）")
    log(f"待测试 URL: {len(sqlmap_urls)} 个")
    log("预计总时间: 8-15分钟")
    
    try:
        tool_path = get_tool_path('sqlmap_scanner')
        
        result = subprocess.run([
            sys.executable,
            str(tool_path),
            os.path.abspath(urls_file),
            os.path.abspath(output_dir)
        ], cwd=os.getcwd(), timeout=TIMEOUT_SQLMAP)
        
        if result.returncode == 0:
            log("[✓] SQLMap 测试完成")
        else:
            log(f"[!] SQLMap 测试返回码 {result.returncode}")
        
        # 读取测试结果
        results_file = os.path.join(output_dir, 'sqlmap_results.json')
        if os.path.exists(results_file):
            try:
                with open(results_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    results = data.get('results', [])
                    vulnerable_count = sum(1 for r in results if r.get('vulnerable'))
                    log(f"测试总数: {len(results)}, 发现漏洞: {vulnerable_count}")
                    return results
            except Exception as e:
                log(f"读取结果文件失败: {e}")
                return []
        else:
            log("未找到 SQLMap 结果文件")
            return []
            
    except subprocess.TimeoutExpired:
        log("[✗] SQLMap 测试超时（20分钟）")
        return []
    except Exception as e:
        log(f"[✗] SQLMap 测试异常: {e}")
        return []

if __name__ == '__main__':
    # 如果提供了命令行参数，使用参数
    if len(sys.argv) >= 3:
        urls_file = sys.argv[1]
        output_dir = sys.argv[2]
    else:
        # 否则从默认位置读取
        from core.utils import get_domain, get_bounty_dir, read_urls_from_file
        
        # 先读取目标 URL 确定输出目录
        target_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'urls', 'first_target.txt')
        targets = read_urls_from_file(target_file)
        
        if not targets:
            print("错误: 未在 urls/first_target.txt 中找到 URL")
            sys.exit(1)
        
        domain = get_domain(targets[0])
        output_dir = get_bounty_dir(domain)
        
        # 默认的 sqlmap_targets.txt 路径
        urls_file = os.path.join(output_dir, 'sqlmap_targets.txt')
        
        if not os.path.exists(urls_file):
            print(f"错误: 找不到 {urls_file}")
            print("请先运行 url_analyzer.py 生成 SQLMap 目标文件")
            sys.exit(1)
        
        print(f"使用 SQLMap 目标文件: {urls_file}")
        print(f"输出目录: {output_dir}\n")
    
    results = test_sql_injection(urls_file, output_dir)
    print(f"\n测试完成，共 {len(results)} 个结果")
