#!/usr/bin/env python3
"""
主入口 - 整合所有模块
完全替代原来的 automate_scan.py
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.utils import setup_encoding, log, load_env_file, get_domain, get_bounty_dir, ensure_dir, read_urls_from_file
from core.config import URLS_DIR
from tools.updater import update_all
from modules.tech_detect import detect_tech_stack
from modules.url_collector import collect_urls
from modules.url_analyzer import analyze_urls
from modules.vuln_scanner import scan_vulnerabilities
from modules.js_analyzer import analyze_js_files
from modules.sqlmap_test import test_sql_injection
from report.generator import generate_report

def scan_single_url(url, base_dir='.'):
    """
    扫描单个 URL
    
    Args:
        url: 目标 URL
        base_dir: 基础目录
    """
    log(f"开始扫描: {url}")
    
    domain = get_domain(url)
    bounty_dir = get_bounty_dir(domain, base_dir)
    
    # 创建目录
    if not os.path.exists(bounty_dir):
        ensure_dir(bounty_dir)
        log(f"创建目录 {bounty_dir}")
    
    # 步骤1: 技术栈检测
    log("\n" + "="*60)
    log("[步骤1/6] 开始: HTTP 探测")
    log("="*60)
    tech_result = detect_tech_stack(url, bounty_dir)
    tech_stack = tech_result.get('tech_stack', [])
    
    # 步骤2: URL 收集
    log("\n" + "="*60)
    log("[步骤2/6] 开始: URL 收集")
    log("="*60)
    all_urls = collect_urls(url, bounty_dir)
    
    if not all_urls:
        log("未收集到 URL，跳过后续步骤")
        return
    
    all_urls_file = os.path.join(bounty_dir, 'all_urls.txt')
    
    # 步骤3: URL 分类分析
    log("\n" + "="*60)
    log("[步骤3/6] 开始: URL 分类分析")
    log("="*60)
    analyze_urls(all_urls_file, bounty_dir)
    
    # 步骤4: Nuclei 漏洞扫描
    log("\n" + "="*60)
    log("[步骤4/6] 开始: Nuclei 漏洞扫描")
    log("="*60)
    scan_vulnerabilities(url, bounty_dir)
    
    # 步骤5: JavaScript 文件分析
    log("\n" + "="*60)
    log("[步骤5/6] 开始: JavaScript 文件分析")
    log("="*60)
    analyze_js_files(all_urls_file, bounty_dir)
    
    # 步骤6: SQLMap 注入测试
    sqlmap_targets_file = os.path.join(bounty_dir, 'sqlmap_targets.txt')
    if os.path.exists(sqlmap_targets_file):
        log("\n" + "="*60)
        log("[步骤6/6] 开始: SQLMap 注入测试")
        log("="*60)
        test_sql_injection(sqlmap_targets_file, bounty_dir)
    else:
        log("\n[INFO] 跳过 SQLMap 测试（无带参数的目标 URL）")
    
    # 生成报告
    log("\n" + "="*60)
    log("[最后步骤] 生成扫描报告")
    log("="*60)
    generate_report(bounty_dir, url, tech_stack, all_urls)

def main():
    # 设置编码
    setup_encoding()
    
    # 加载环境变量
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if load_env_file(env_file):
        log("[OK] 已加载 .env 配置文件")
    
    # 显示欢迎信息
    log("="*60)
    log("自动化安全扫描器 v2.0 (模块化版本)")
    log("="*60)
    
    # 更新工具
    log("\n[INFO] 检查工具更新...")
    update_all()
    
    # 检查 URLs 目录
    if not os.path.exists(URLS_DIR):
        log("urls/ 目录不存在。")
        return
    
    # 遍历所有 URL 文件
    for file in os.listdir(URLS_DIR):
        if file.endswith('.txt'):
            file_path = os.path.join(URLS_DIR, file)
            urls = read_urls_from_file(file_path)
            
            if not urls:
                log(f"文件 {file} 中没有有效的 URL")
                continue
            
            log(f"\n从 {file} 加载 {len(urls)} 个 URL")
            
            # 扫描每个 URL
            for url in urls:
                try:
                    scan_single_url(url)
                except Exception as e:
                    log(f"[ERROR] 扫描 {url} 时发生错误: {e}")
                    import traceback
                    log(traceback.format_exc())

if __name__ == "__main__":
    main()
