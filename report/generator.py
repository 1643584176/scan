#!/usr/bin/env python3
"""
报告生成模块
可以单独运行: python report/generator.py <bounty_dir> <url> <tech_stack> <urls_count>
"""
import sys
import os
import json
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.utils import log, read_urls_from_file

def generate_report(bounty_dir, url, tech_stack=None, all_urls=None):
    """
    生成扫描报告
    
    Args:
        bounty_dir: bounty 目录
        url: 目标 URL
        tech_stack: 技术栈列表
        all_urls: URL 列表
    
    Returns:
        bool: 是否成功
    """
    findings_path = os.path.join(bounty_dir, 'findings.md')
    progress_path = os.path.join(bounty_dir, 'progress.md')
    readme_path = os.path.join(bounty_dir, 'README.md')
    
    # 读取 SQLMap 结果
    sqlmap_results = []
    sqlmap_results_file = os.path.join(bounty_dir, 'sqlmap_results.json')
    if os.path.exists(sqlmap_results_file):
        try:
            with open(sqlmap_results_file, 'r', encoding='utf-8') as f:
                sqlmap_data = json.load(f)
                sqlmap_results = sqlmap_data.get('results', [])
        except:
            pass
    
    # 读取 Nuclei 扫描结果
    nuclei_results = []
    nuclei_file = os.path.join(bounty_dir, 'nuclei_scan.txt')
    if os.path.exists(nuclei_file):
        try:
            with open(nuclei_file, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = [line.strip() for line in content.splitlines() if line.strip()]
                nuclei_results = lines
        except:
            pass
    
    # 如果没有提供 URLs，尝试读取
    if all_urls is None:
        all_urls_file = os.path.join(bounty_dir, 'all_urls.txt')
        if os.path.exists(all_urls_file):
            all_urls = read_urls_from_file(all_urls_file)
        else:
            all_urls = []
    
    # 更新 findings.md
    log("生成 findings.md...")
    with open(findings_path, 'a', encoding='utf-8') as f:
        f.write(f"\n## {url} 扫描结果\n")
        f.write(f"**扫描时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("### 技术栈\n")
        if tech_stack:
            for tech in tech_stack:
                f.write(f"- {tech}\n")
        else:
            f.write("- 未检测\n")
        f.write("\n")
        
        f.write("### URL 分类统计\n")
        f.write(f"- **总 URL 数**: {len(all_urls)}\n")
        f.write(f"- **API 端点**: {len([u for u in all_urls if '/api/' in u.lower() or u.lower().endswith('.json')])}\n")
        f.write(f"- **带参数页面**: {len([u for u in all_urls if '?' in u])}\n")
        f.write(f"- **登录/认证**: {len([u for u in all_urls if any(k in u.lower() for k in ['/login', '/auth', '/signin'])])}\n")
        f.write(f"- **管理后台**: {len([u for u in all_urls if any(k in u.lower() for k in ['/admin', '/dashboard'])])}\n\n")
        
        # Nuclei 漏洞扫描结果
        if nuclei_results:
            f.write("### Nuclei 漏洞扫描\n\n")
            f.write(f"- **发现漏洞**: {len(nuclei_results)} 个\n\n")
            f.write("#### 漏洞详情:\n\n")
            for i, vuln in enumerate(nuclei_results[:20], 1):
                f.write(f"{i}. `{vuln[:150]}`\n")
            if len(nuclei_results) > 20:
                f.write(f"\n... 还有 {len(nuclei_results) - 20} 个漏洞\n")
            f.write("\n")
        else:
            f.write("### Nuclei 漏洞扫描\n\n")
            f.write("- 未发现明显漏洞\n\n")
        
        if sqlmap_results:
            f.write("### SQLMap 注入测试\n\n")
            vulnerable_count = sum(1 for r in sqlmap_results if r.get('vulnerable'))
            f.write(f"- **测试总数**: {len(sqlmap_results)}\n")
            f.write(f"- **发现漏洞**: {vulnerable_count}\n\n")
            
            if vulnerable_count > 0:
                f.write("#### 发现的注入点:\n\n")
                for i, result in enumerate(sqlmap_results, 1):
                    if result.get('vulnerable'):
                        f.write(f"{i}. `{result['url'][:100]}`\n")
                f.write("\n")
        else:
            f.write("### SQLMap 测试\n\n")
            f.write("- 无带参数的 URL，跳过 SQLMap 测试\n\n")
        
        f.write("---\n\n")
    
    # 更新 progress.md
    log("更新 progress.md...")
    with open(progress_path, 'a', encoding='utf-8') as f:
        f.write(f"- {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: 扫描 {url} 完成\n")
    
    # 更新 README.md
    log("更新 README.md...")
    with open(readme_path, 'a', encoding='utf-8') as f:
        f.write(f"\n## 扫描总结 - {url}\n\n")
        f.write(f"**扫描时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"- **目标**: {url}\n")
        f.write(f"- **技术栈**: {', '.join(tech_stack) if tech_stack else '未检测'}\n")
        f.write(f"- **URL 数量**: {len(all_urls)}\n")
        f.write(f"- **Nuclei 漏洞**: {len(nuclei_results)} 个\n")
        f.write(f"- **SQLMap 测试**: {len(sqlmap_results)} 个 URL\n\n")
    
    log("[✓] 报告生成完成")
    return True

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("用法: python report/generator.py <bounty_dir> <url> [tech_stack_json] [urls_file]")
        sys.exit(1)
    
    bounty_dir = sys.argv[1]
    url = sys.argv[2]
    
    tech_stack = None
    if len(sys.argv) > 3:
        try:
            tech_stack = json.loads(sys.argv[3])
        except:
            tech_stack = []
    
    all_urls = None
    if len(sys.argv) > 4:
        urls_file = sys.argv[4]
        if os.path.exists(urls_file):
            all_urls = read_urls_from_file(urls_file)
    
    success = generate_report(bounty_dir, url, tech_stack, all_urls)
    sys.exit(0 if success else 1)
