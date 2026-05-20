#!/usr/bin/env python3
"""
HackerOne API 集成模块
用于获取目标范围、提交漏洞报告等
"""

import os
import requests
import json
from typing import List, Dict, Optional


class HackerOneAPI:
    """HackerOne API 客户端"""
    
    def __init__(self, api_token: str = None, username: str = None):
        """
        初始化 HackerOne API 客户端
        
        Args:
            api_token: HackerOne API Token（从 https://hackerone.com/settings/api_token 获取）
            username: HackerOne 用户名
        """
        self.api_token = api_token or os.environ.get('HACKERONE_API_TOKEN')
        self.username = username or os.environ.get('HACKERONE_USERNAME')
        
        if not self.api_token or not self.username:
            raise ValueError(
                "请设置 HACKERONE_API_TOKEN 和 HACKERONE_USERNAME 环境变量，"
                "或在初始化时传入参数"
            )
        
        self.base_url = 'https://api.hackerone.com/v1'
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        # 使用 Basic Auth
        from base64 import b64encode
        auth_string = f'{self.username}:{self.api_token}'
        self.headers['Authorization'] = f'Basic {b64encode(auth_string.encode()).decode()}'
    
    def get_programs(self) -> List[Dict]:
        """
        获取你参与的所有漏洞赏金项目
        
        Returns:
            项目列表
        """
        url = f'{self.base_url}/me/programs'
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json().get('data', [])
    
    def get_program_scopes(self, program_handle: str) -> Dict:
        """
        获取指定项目的目标范围
        
        Args:
            program_handle: 项目标识（如 'shopify'）
            
        Returns:
            包含 in_scope 和 out_of_scope 的字典
        """
        url = f'{self.base_url}/programs/{program_handle}'
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        data = response.json().get('data', {})
        attributes = data.get('attributes', {})
        
        return {
            'in_scope': attributes.get('structured_scopes', []),
            'out_of_scope': attributes.get('out_of_scope', []),
            'policy': attributes.get('policy_html', ''),
        }
    
    def get_in_scope_domains(self, program_handle: str) -> List[str]:
        """
        获取项目中所有在范围内的域名
        
        Args:
            program_handle: 项目标识
            
        Returns:
            域名列表
        """
        scopes = self.get_program_scopes(program_handle)
        domains = []
        
        for scope in scopes.get('in_scope', []):
            asset_type = scope.get('asset_type')
            asset_identifier = scope.get('asset_identifier', '')
            
            # 只获取域名类型的资产
            if asset_type == 'URL' and asset_identifier:
                # 提取域名
                from urllib.parse import urlparse
                parsed = urlparse(asset_identifier)
                domain = parsed.netloc or parsed.path
                if domain:
                    domains.append(domain)
        
        return list(set(domains))  # 去重
    
    def create_report(self, program_handle: str, title: str, vulnerability_type: str, 
                     severity: str, description: str, impact: str, 
                     steps_to_reproduce: str, urls: List[str] = None) -> Dict:
        """
        创建新的漏洞报告
        
        Args:
            program_handle: 项目标识
            title: 漏洞标题
            vulnerability_type: 漏洞类型（如 'XSS', 'SQL Injection'）
            severity: 严重程度（critical/high/medium/low）
            description: 漏洞描述
            impact: 影响说明
            steps_to_reproduce: 复现步骤
            urls: 相关 URL 列表
            
        Returns:
            创建的报告信息
        """
        url = f'{self.base_url}/reports'
        
        # 映射严重程度到数值
        severity_map = {
            'critical': 5,
            'high': 4,
            'medium': 3,
            'low': 2,
            'none': 1
        }
        
        payload = {
            'data': {
                'type': 'report',
                'attributes': {
                    'team_id': program_handle,
                    'title': title,
                    'vulnerability_type': vulnerability_type,
                    'severity_rating': severity_map.get(severity, 3),
                    'description': description,
                    'impact': impact,
                    'steps_to_reproduce': steps_to_reproduce,
                }
            }
        }
        
        # 添加 URL 附件
        if urls:
            attachments = []
            for i, url in enumerate(urls, 1):
                attachments.append({
                    'filename': f'url_{i}.txt',
                    'content': url
                })
            payload['data']['attributes']['attachments'] = attachments
        
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json().get('data', {})
    
    def get_reports(self, status: str = None, limit: int = 100) -> List[Dict]:
        """
        获取你的漏洞报告列表
        
        Args:
            status: 过滤状态（new/triage/in_progress/resolved/closed）
            limit: 返回数量限制
            
        Returns:
            报告列表
        """
        url = f'{self.base_url}/me/reports'
        params = {'limit': limit}
        
        if status:
            params['filter[status]'] = status
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json().get('data', [])
    
    def search_vulnerabilities(self, keyword: str, limit: int = 50) -> List[Dict]:
        """
        搜索公开的漏洞报告（用于学习）
        
        Args:
            keyword: 搜索关键词
            limit: 返回数量限制
            
        Returns:
            漏洞报告列表
        """
        url = f'{self.base_url}/hackathons'  # HackerOne 没有公开的漏洞搜索 API
        # 注意：HackerOne API 不支持搜索公开漏洞
        # 这个功能需要通过网页爬取实现（不推荐）
        return []


def load_targets_from_hackerone(program_handles: List[str] = None) -> List[str]:
    """
    从 HackerOne 加载目标域名
    
    Args:
        program_handles: 要获取的项目列表，如果为 None 则获取所有项目
        
    Returns:
        目标域名列表
    """
    try:
        client = HackerOneAPI()
    except ValueError as e:
        print(f"[WARN] 无法连接 HackerOne: {e}")
        print("[INFO] 请在环境变量中设置 HACKERONE_API_TOKEN 和 HACKERONE_USERNAME")
        return []
    
    all_domains = []
    
    if program_handles:
        # 获取指定项目
        for handle in program_handles:
            try:
                print(f"[INFO] 获取项目 {handle} 的目标范围...")
                domains = client.get_in_scope_domains(handle)
                all_domains.extend(domains)
                print(f"[OK] {handle}: 找到 {len(domains)} 个域名")
            except Exception as e:
                print(f"[ERROR] 获取 {handle} 失败: {e}")
    else:
        # 获取所有项目
        print("[INFO] 获取所有项目...")
        programs = client.get_programs()
        print(f"[OK] 找到 {len(programs)} 个项目")
        
        for program in programs[:5]:  # 只获取前5个项目，避免太多
            handle = program.get('attributes', {}).get('handle')
            if handle:
                try:
                    domains = client.get_in_scope_domains(handle)
                    all_domains.extend(domains)
                    print(f"[OK] {handle}: {len(domains)} 个域名")
                except Exception as e:
                    print(f"[WARN] {handle}: {e}")
    
    return list(set(all_domains))  # 去重


if __name__ == "__main__":
    # 测试代码
    print("HackerOne API 测试")
    print("="*60)
    
    try:
        client = HackerOneAPI()
        
        # 获取项目列表
        print("\n1. 获取项目列表...")
        programs = client.get_programs()
        print(f"   找到 {len(programs)} 个项目")
        
        if programs:
            first_program = programs[0]['attributes']['handle']
            print(f"\n2. 获取第一个项目 ({first_program}) 的目标范围...")
            domains = client.get_in_scope_domains(first_program)
            print(f"   找到 {len(domains)} 个域名")
            if domains:
                print(f"   示例: {domains[:3]}")
        
        # 获取报告列表
        print("\n3. 获取最近的报告...")
        reports = client.get_reports(limit=5)
        print(f"   找到 {len(reports)} 个报告")
        
    except ValueError as e:
        print(f"配置错误: {e}")
        print("\n请设置环境变量:")
        print("  export HACKERONE_API_TOKEN='your_token'")
        print("  export HACKERONE_USERNAME='your_username'")
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
