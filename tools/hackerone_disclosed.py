#!/usr/bin/env python3
"""
HackerOne 公开漏洞报告查询模块
用于学习和研究已公开的漏洞报告
"""

import requests
import json
import time
from typing import List, Dict, Optional
from datetime import datetime


class HackerOneDisclosed:
    """HackerOne 公开报告查询器"""
    
    def __init__(self):
        """初始化公开报告查询器"""
        self.base_url = 'https://hackerone.com'
        self.api_url = 'https://api.hackerone.com/v1'
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def search_disclosed_reports(self, query: str = None, 
                                 vulnerability_type: str = None,
                                 severity: str = None,
                                 program: str = None,
                                 limit: int = 50) -> List[Dict]:
        """
        搜索公开的漏洞报告
        
        Args:
            query: 搜索关键词（如 'XSS', 'SQL Injection'）
            vulnerability_type: 漏洞类型过滤
            severity: 严重程度过滤 (critical/high/medium/low)
            program: 项目名称过滤
            limit: 返回数量限制
            
        Returns:
            公开报告列表
        """
        # 注意：HackerOne 没有官方的公开报告搜索 API
        # 这里使用网页爬取方式（仅供学习研究）
        
        reports = []
        
        try:
            # 构建搜索 URL
            search_url = f'{self.base_url}/directory/reports'
            params = {
                'disclosed': 'true',
                'limit': limit
            }
            
            if query:
                params['query'] = query
            
            if vulnerability_type:
                params['vulnerability_type'] = vulnerability_type
            
            if severity:
                params['severity'] = severity
            
            if program:
                params['program'] = program
            
            print(f"[INFO] 搜索公开报告...")
            print(f"   关键词: {query or '全部'}")
            print(f"   类型: {vulnerability_type or '全部'}")
            print(f"   严重程度: {severity or '全部'}")
            
            response = self.session.get(search_url, params=params, timeout=30)
            
            if response.status_code == 200:
                # 解析 HTML 获取报告列表
                # 注意：这需要 HTML 解析，这里提供简化版本
                print(f"[OK] 找到报告（需要进一步解析）")
                return []
            else:
                print(f"[ERROR] 请求失败: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"[ERROR] 搜索失败: {e}")
            return []
    
    def get_report_details(self, report_id: str) -> Optional[Dict]:
        """
        获取单个公开报告的详细信息
        
        Args:
            report_id: 报告 ID
            
        Returns:
            报告详情
        """
        try:
            url = f'{self.base_url}/reports/{report_id}'
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                # 解析报告详情
                # 这里需要 HTML 解析来提取内容
                print(f"[INFO] 获取报告 {report_id} 详情")
                return {'id': report_id, 'url': url}
            else:
                print(f"[ERROR] 无法获取报告 {report_id}")
                return None
                
        except Exception as e:
            print(f"[ERROR] 获取报告详情失败: {e}")
            return None
    
    def get_program_disclosed_reports(self, program_handle: str, 
                                      limit: int = 20) -> List[Dict]:
        """
        获取指定项目的公开报告
        
        Args:
            program_handle: 项目标识（如 'shopify'）
            limit: 返回数量限制
            
        Returns:
            公开报告列表
        """
        try:
            url = f'{self.base_url}/{program_handle}/reports/disclosed'
            params = {'limit': limit}
            
            print(f"[INFO] 获取 {program_handle} 的公开报告...")
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                print(f"[OK] 获取成功")
                # 需要解析 HTML
                return []
            else:
                print(f"[ERROR] 请求失败: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"[ERROR] 获取失败: {e}")
            return []
    
    def export_reports_to_json(self, reports: List[Dict], filename: str = 'disclosed_reports.json'):
        """
        导出报告到 JSON 文件
        
        Args:
            reports: 报告列表
            filename: 输出文件名
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(reports, f, ensure_ascii=False, indent=2)
            print(f"[OK] 已导出 {len(reports)} 个报告到 {filename}")
        except Exception as e:
            print(f"[ERROR] 导出失败: {e}")
    
    def analyze_vulnerability_patterns(self, reports: List[Dict]) -> Dict:
        """
        分析漏洞模式和趋势
        
        Args:
            reports: 报告列表
            
        Returns:
            分析结果
        """
        patterns = {
            'total_reports': len(reports),
            'by_severity': {},
            'by_type': {},
            'common_keywords': [],
            'avg_bounty': 0
        }
        
        # 统计严重程度分布
        for report in reports:
            severity = report.get('severity', 'unknown')
            patterns['by_severity'][severity] = patterns['by_severity'].get(severity, 0) + 1
            
            vuln_type = report.get('vulnerability_type', 'unknown')
            patterns['by_type'][vuln_type] = patterns['by_type'].get(vuln_type, 0) + 1
        
        return patterns


def search_and_save_reports(query: str = None, 
                           vulnerability_type: str = None,
                           severity: str = None,
                           program: str = None,
                           limit: int = 50,
                           output_file: str = 'disclosed_reports.json'):
    """
    搜索公开报告并保存到文件
    
    Args:
        query: 搜索关键词
        vulnerability_type: 漏洞类型
        severity: 严重程度
        program: 项目名称
        limit: 数量限制
        output_file: 输出文件
    """
    searcher = HackerOneDisclosed()
    
    print("="*60)
    print("HackerOne 公开漏洞报告搜索")
    print("="*60)
    
    # 搜索报告
    reports = searcher.search_disclosed_reports(
        query=query,
        vulnerability_type=vulnerability_type,
        severity=severity,
        program=program,
        limit=limit
    )
    
    if reports:
        # 导出到文件
        searcher.export_reports_to_json(reports, output_file)
        
        # 分析模式
        patterns = searcher.analyze_vulnerability_patterns(reports)
        
        print("\n" + "="*60)
        print("分析报告")
        print("="*60)
        print(f"总报告数: {patterns['total_reports']}")
        print(f"\n严重程度分布:")
        for sev, count in patterns['by_severity'].items():
            print(f"  {sev}: {count}")
        
        print(f"\n漏洞类型分布:")
        for vtype, count in patterns['by_type'].items():
            print(f"  {vtype}: {count}")
    else:
        print("[WARN] 未找到报告或需要手动解析")


if __name__ == "__main__":
    import sys
    
    print("HackerOne 公开报告查询工具")
    print("="*60)
    
    # 默认搜索最近的 XSS 报告
    query = 'XSS'
    vuln_type = None
    severity = 'high'
    program = None
    limit = 20
    
    # 支持命令行参数
    if len(sys.argv) > 1:
        query = sys.argv[1]
    if len(sys.argv) > 2:
        severity = sys.argv[2]
    if len(sys.argv) > 3:
        limit = int(sys.argv[3])
    
    print(f"\n搜索参数:")
    print(f"  关键词: {query}")
    print(f"  严重程度: {severity}")
    print(f"  数量限制: {limit}\n")
    
    search_and_save_reports(
        query=query,
        severity=severity,
        limit=limit,
        output_file=f'disclosed_{query.lower()}_reports.json'
    )
    
    print("\n" + "="*60)
    print("提示: 由于 HackerOne 没有官方公开报告 API，")
    print("      完整功能需要使用网页爬虫实现。")
    print("      建议直接访问: https://hackerone.com/directory/reports?disclosed=true")
    print("="*60)
