#!/usr/bin/env python3
"""
主入口 - 整合所有模块
完全替代原来的 automate_scan.py
"""
import sys
import os
import concurrent.futures
from functools import partial

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
    
    # 可选的工具更新（通过环境变量控制）
    skip_update = os.environ.get('SKIP_UPDATE', 'false').lower() == 'true'
    if not skip_update:
        log("\n[INFO] 检查工具更新...")
        update_all()
    else:
        log("\n[INFO] 跳过工具更新检查（SKIP_UPDATE=true）")
    
    # 检查 URLs 目录
    if not os.path.exists(URLS_DIR):
        log("urls/ 目录不存在。")
        return
    
    # 收集所有待扫描的 URL
    all_targets = []
    for file in os.listdir(URLS_DIR):
        if file.endswith('.txt'):
            file_path = os.path.join(URLS_DIR, file)
            urls = read_urls_from_file(file_path)
            
            if not urls:
                log(f"文件 {file} 中没有有效的 URL")
                continue
            
            log(f"\n从 {file} 加载 {len(urls)} 个 URL")
            all_targets.extend(urls)
    
    if not all_targets:
        log("\n[WARN] 没有找到任何待扫描的目标")
        return
    
    # 并行扫描配置
    max_workers = int(os.environ.get('SCAN_WORKERS', '2'))  # 默认2个并发
    log(f"\n[INFO] 使用 {max_workers} 个并发线程扫描 {len(all_targets)} 个目标")
    log("[TIP] 可通过环境变量 SCAN_WORKERS 调整并发数（建议1-3，避免对目标造成压力）")
    
    # 使用线程池并行扫描
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有扫描任务
        future_to_url = {
            executor.submit(scan_single_url, url): url 
            for url in all_targets
        }
        
        # 处理完成的任务
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                future.result()
                log(f"\n[OK] {url} 扫描完成\n")
            except Exception as e:
                log(f"\n[ERROR] 扫描 {url} 时发生错误: {e}")
                import traceback
                log(traceback.format_exc())
    
    log("\n" + "="*60)
    log("所有目标扫描完成！")
    log("="*60)

if __name__ == "__main__":
    main()
