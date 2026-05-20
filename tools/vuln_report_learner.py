#!/usr/bin/env python3
"""
漏洞报告学习助手
从 HackerOne 获取公开报告，分析漏洞模式和利用技巧
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from typing import List, Dict
from urllib.parse import urljoin


class VulnerabilityReportLearner:
    """漏洞报告学习助手"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def fetch_disclosed_reports_page(self, page: int = 1) -> List[Dict]:
        """
        获取公开报告列表页面
        
        Args:
            page: 页码
            
        Returns:
            报告摘要列表
        """
        url = f'https://hackerone.com/directory/reports?disclosed=true&page={page}'
        
        try:
            response = self.session.get(url, timeout=30)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                reports = []
                # 解析报告卡片（需要根据实际 HTML 结构调整）
                report_cards = soup.find_all('div', class_='card')  # 示例选择器
                
                for card in report_cards[:10]:  # 每页最多10个
                    report = self._parse_report_card(card)
                    if report:
                        reports.append(report)
                
                return reports
            else:
                print(f"[ERROR] 请求失败: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"[ERROR] 获取页面失败: {e}")
            return []
    
    def _parse_report_card(self, card) -> Dict:
        """解析报告卡片"""
        try:
            # 提取报告信息（需要根据实际 HTML 结构）
            title_elem = card.find('a', class_='report-title')
            program_elem = card.find('span', class_='program-name')
            severity_elem = card.find('span', class_='severity')
            
            if title_elem:
                return {
                    'title': title_elem.get_text(strip=True),
                    'url': urljoin('https://hackerone.com', title_elem.get('href', '')),
                    'program': program_elem.get_text(strip=True) if program_elem else '',
                    'severity': severity_elem.get_text(strip=True) if severity_elem else '',
                }
        except:
            pass
        
        return None
    
    def fetch_report_details(self, report_url: str) -> Dict:
        """
        获取单个报告的详细信息
        
        Args:
            report_url: 报告 URL
            
        Returns:
            报告详情
        """
        try:
            print(f"[INFO] 获取报告详情: {report_url}")
            response = self.session.get(report_url, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 提取报告内容
                details = {
                    'url': report_url,
                    'title': '',
                    'vulnerability_type': '',
                    'severity': '',
                    'description': '',
                    'impact': '',
                    'steps_to_reproduce': '',
                    'remediation': '',
                }
                
                # 提取标题
                title_elem = soup.find('h1')
                if title_elem:
                    details['title'] = title_elem.get_text(strip=True)
                
                # 提取漏洞描述
                desc_sections = soup.find_all('div', class_='report-section')
                for section in desc_sections:
                    heading = section.find('h3')
                    if heading:
                        heading_text = heading.get_text(strip=True).lower()
                        content = section.find('div', class_='content')
                        
                        if content:
                            if 'description' in heading_text or '描述' in heading_text:
                                details['description'] = content.get_text(strip=True)[:500]
                            elif 'impact' in heading_text or '影响' in heading_text:
                                details['impact'] = content.get_text(strip=True)[:500]
                            elif 'reproduction' in heading_text or '复现' in heading_text:
                                details['steps_to_reproduce'] = content.get_text(strip=True)[:500]
                
                return details
            else:
                print(f"[ERROR] 无法获取报告")
                return {}
                
        except Exception as e:
            print(f"[ERROR] 获取详情失败: {e}")
            return {}
    
    def search_by_vulnerability_type(self, vuln_type: str, limit: int = 10) -> List[Dict]:
        """
        按漏洞类型搜索报告
        
        Args:
            vuln_type: 漏洞类型（如 'XSS', 'SQL Injection', 'IDOR'）
            limit: 数量限制
            
        Returns:
            报告列表
        """
        print(f"\n{'='*60}")
        print(f"搜索 {vuln_type} 漏洞报告")
        print(f"{'='*60}\n")
        
        all_reports = []
        page = 1
        
        while len(all_reports) < limit and page <= 5:  # 最多搜索5页
            print(f"[INFO] 正在搜索第 {page} 页...")
            
            reports = self.fetch_disclosed_reports_page(page)
            
            # 过滤指定类型的报告
            filtered = [r for r in reports if vuln_type.lower() in r.get('title', '').lower()]
            all_reports.extend(filtered)
            
            if not reports:  # 没有更多报告
                break
            
            page += 1
            time.sleep(2)  # 避免请求过快
        
        return all_reports[:limit]
    
    def generate_learning_report(self, reports: List[Dict], output_file: str = 'learning_report.md'):
        """
        生成学习报告
        
        Args:
            reports: 报告列表
            output_file: 输出文件
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# HackerOne 漏洞报告学习笔记\n\n")
            f.write(f"**生成时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**报告数量**: {len(reports)}\n\n")
            
            f.write("---\n\n")
            
            for i, report in enumerate(reports, 1):
                f.write(f"## {i}. {report.get('title', 'Unknown')}\n\n")
                f.write(f"- **项目**: {report.get('program', 'N/A')}\n")
                f.write(f"- **严重程度**: {report.get('severity', 'N/A')}\n")
                f.write(f"- **链接**: [{report.get('url', '')}]({report.get('url', '')})\n\n")
                
                if 'description' in report:
                    f.write("### 漏洞描述\n\n")
                    f.write(f"{report['description']}\n\n")
                
                if 'impact' in report:
                    f.write("### 影响\n\n")
                    f.write(f"{report['impact']}\n\n")
                
                if 'steps_to_reproduce' in report:
                    f.write("### 复现步骤\n\n")
                    f.write(f"{report['steps_to_reproduce']}\n\n")
                
                f.write("---\n\n")
        
        print(f"[OK] 学习报告已保存到: {output_file}")
    
    def analyze_common_patterns(self, reports: List[Dict]) -> Dict:
        """
        分析常见漏洞模式
        
        Args:
            reports: 报告列表
            
        Returns:
            分析结果
        """
        patterns = {
            'total_analyzed': len(reports),
            'common_locations': [],
            'common_techniques': [],
            'prevention_tips': []
        }
        
        # 这里可以添加更复杂的分析逻辑
        # 例如：提取常见的漏洞位置、利用技术等
        
        return patterns


def main():
    """主函数"""
    import sys
    
    print("="*60)
    print("HackerOne 漏洞报告学习助手")
    print("="*60)
    
    learner = VulnerabilityReportLearner()
    
    # 默认搜索 XSS 报告
    vuln_type = 'XSS'
    limit = 5
    
    if len(sys.argv) > 1:
        vuln_type = sys.argv[1]
    if len(sys.argv) > 2:
        limit = int(sys.argv[2])
    
    print(f"\n搜索参数:")
    print(f"  漏洞类型: {vuln_type}")
    print(f"  数量限制: {limit}\n")
    
    # 搜索报告
    reports = learner.search_by_vulnerability_type(vuln_type, limit)
    
    if reports:
        print(f"\n[OK] 找到 {len(reports)} 个报告")
        
        # 生成学习报告
        output_file = f'{vuln_type.lower()}_learning_report.md'
        learner.generate_learning_report(reports, output_file)
        
        # 显示摘要
        print(f"\n报告摘要:")
        for i, report in enumerate(reports, 1):
            print(f"{i}. {report.get('title', 'N/A')[:60]}")
            print(f"   项目: {report.get('program', 'N/A')}")
            print(f"   链接: {report.get('url', '')}")
            print()
    else:
        print("[WARN] 未找到报告")
        print("\n提示:")
        print("  1. 直接访问: https://hackerone.com/directory/reports?disclosed=true")
        print("  2. 使用浏览器扩展手动收集报告")
        print("  3. 考虑使用 HackerOne API（需要认证）")


if __name__ == "__main__":
    main()
