#!/usr/bin/env python3
"""
子域名枚举工具
使用多种方法发现目标域名的子域名
用法: python subdomain_enum.py <目标域名> [输出目录]
"""

import sys
import os
import warnings
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONUTF8'] = '1'
    # 设置 Windows 控制台编码
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    except:
        pass

warnings.filterwarnings('ignore')  # 抑制所有警告

import subprocess
import json
import time
from datetime import datetime
from urllib.parse import urlparse

def log(message):
    """输出带时间戳的日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")

def extract_domain(url):
    """从URL提取主域名"""
    parsed = urlparse(url)
    domain = parsed.netloc
    
    # 移除端口号
    if ':' in domain:
        domain = domain.split(':')[0]
    
    # 移除 www. 前缀
    if domain.startswith('www.'):
        domain = domain[4:]
    
    return domain

def run_subfinder(domain, output_dir):
    """使用 Subfinder 进行子域名枚举"""
    log("[SUBFINDER] 启动 Subfinder 子域名枚举...")
    
    subfinder_exe = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'nuclei', 'subfinder.exe')
    
    # 如果 subfinder.exe 不存在，尝试从 PATH 查找
    if not os.path.exists(subfinder_exe):
        subfinder_exe = 'subfinder'
        # 检查是否在 PATH 中
        try:
            result = subprocess.run(['where', 'subfinder'], capture_output=True)
            if result.returncode != 0:
                log("[WARN] Subfinder 未安装，跳过此步骤")
                log("[INFO] 安装方法: go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest")
                return []
        except:
            log("[WARN] Subfinder 未安装，跳过此步骤")
            return []
    
    output_file = os.path.join(output_dir, 'subdomains_raw.txt')
    
    cmd = [
        subfinder_exe,
        '-d', domain,
        '-o', output_file,
        '-silent',
        '-t', '50',  # 线程数
        '-timeout', '30',  # 超时时间
        '-max-time', '300'  # 最大运行时间5分钟
    ]
    
    try:
        log(f"   [CMD] {' '.join(cmd)}")
        # 不使用 text=True 和 encoding，避免编码问题
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=600  # 10分钟总超时
        )
        
        if os.path.exists(output_file):
            with open(output_file, 'r', encoding='utf-8', errors='ignore') as f:
                subdomains = [line.strip() for line in f if line.strip()]
            
            log(f"[OK] Subfinder 发现 {len(subdomains)} 个子域名")
            
            # 显示前10个示例
            if subdomains:
                log(f"   [示例] 前10个子域名:")
                for i, sub in enumerate(subdomains[:10], 1):
                    log(f"      {i}. {sub}")
                if len(subdomains) > 10:
                    log(f"      ... 还有 {len(subdomains) - 10} 个")
            
            return subdomains
        else:
            log("[WARN] Subfinder 未生成输出文件")
            return []
            
    except subprocess.TimeoutExpired:
        log("[ERROR] Subfinder 超时")
        return []
    except Exception as e:
        log(f"[ERROR] Subfinder 执行失败: {e}")
        return []

def run_amass(domain, output_dir):
    """使用 Amass 进行子域名枚举（如果已安装）"""
    log("[AMASS] 尝试使用 Amass 进行子域名枚举...")
    
    amass_exe = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'nuclei', 'amass.exe')
    
    if not os.path.exists(amass_exe):
        amass_exe = 'amass'
        try:
            result = subprocess.run(['where', 'amass'], capture_output=True)
            if result.returncode != 0:
                log("[INFO] Amass 未安装，跳过")
                return []
        except:
            log("[INFO] Amass 未安装，跳过")
            return []
    
    output_file = os.path.join(output_dir, 'amass_subdomains.txt')
    
    cmd = [
        amass_exe,
        'enum',
        '-d', domain,
        '-o', output_file,
        '-passive',  # 仅被动模式，更快
        '-timeout', '5'
    ]
    
    try:
        # 不使用 text=True 和 encoding，避免编码问题
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=600
        )
        
        if os.path.exists(output_file):
            with open(output_file, 'r', encoding='utf-8', errors='ignore') as f:
                subdomains = [line.strip() for line in f if line.strip()]
            
            log(f"[OK] Amass 发现 {len(subdomains)} 个子域名")
            return subdomains
        else:
            return []
            
    except:
        log("[WARN] Amass 执行失败或超时")
        return []

def brute_force_subdomains(domain, output_dir, wordlist_size='small'):
    """暴力破解常见子域名"""
    log("[BRUTE] 开始子域名暴力破解...")
    
    # 常见子域名字典
    common_subdomains = [
        'api', 'www', 'mail', 'ftp', 'admin', 'test', 'dev', 'staging',
        'prod', 'production', 'stage', 'beta', 'alpha', 'demo',
        'app', 'mobile', 'm', 'web', 'portal', 'dashboard',
        'docs', 'documentation', 'help', 'support', 'status',
        'blog', 'news', 'media', 'cdn', 'static', 'assets',
        'img', 'images', 'video', 'videos', 'files', 'download',
        'upload', 'store', 'shop', 'pay', 'payment', 'billing',
        'auth', 'login', 'signin', 'signup', 'register', 'account',
        'user', 'users', 'profile', 'settings', 'config',
        'db', 'database', 'mysql', 'postgres', 'redis', 'mongo',
        'git', 'svn', 'jenkins', 'ci', 'cd', 'build',
        'monitor', 'metrics', 'grafana', 'kibana', 'elastic',
        'vpn', 'proxy', 'gateway', 'lb', 'loadbalancer',
        'internal', 'private', 'secure', 'ssl', 'tls',
        'v1', 'v2', 'v3', 'api-v1', 'api-v2', 'graphql',
        'sandbox', 'testing', 'qa', 'uat', 'preprod',
        'cloud', 'aws', 'azure', 'gcp', 'server', 'node',
        'backup', 'logs', 'analytics', 'tracking', 'pixel',
        'email', 'newsletter', 'marketing', 'crm', 'erp',
        'hr', 'careers', 'jobs', 'recruit', 'talent',
        'legal', 'privacy', 'terms', 'policy', 'compliance',
        'security', 'bugbounty', 'vdp', 'responsible-disclosure',
        'partners', 'partner', 'developer', 'developers',
        'community', 'forum', 'discuss', 'chat', 'slack',
        'events', 'conference', 'meetup', 'webinar',
        'research', 'labs', 'innovation', 'ai', 'ml',
        'data', 'bigdata', 'warehouse', 'lake', 'stream',
        'cache', 'queue', 'worker', 'job', 'task',
        'search', 'solr', 'elasticsearch', 'meilisearch',
        'cms', 'wordpress', 'drupal', 'joomla',
        'shopify', 'woocommerce', 'magento', 'prestashop',
        'jenkins', 'gitlab', 'github', 'bitbucket',
        'docker', 'kubernetes', 'k8s', 'helm', 'istio',
        'prometheus', 'alertmanager', 'consul', 'vault',
        'traefik', 'nginx', 'apache', 'haproxy',
        'rabbitmq', 'kafka', 'zookeeper', 'etcd',
        'sentry', 'newrelic', 'datadog', 'splunk',
        'jira', 'confluence', 'notion', 'trello',
        'zoom', 'teams', 'meet', 'hangouts',
        'stripe', 'paypal', 'square', 'braintree',
        'twilio', 'sendgrid', 'mailchimp', 'intercom',
        'zendesk', 'freshdesk', 'hubspot', 'salesforce',
        'okta', 'auth0', 'firebase', 'supabase',
        'vercel', 'netlify', 'heroku', 'digitalocean',
        'linode', 'vultr', 'ovh', 'hetzner',
        'terraform', 'ansible', 'puppet', 'chef',
        'grafana', 'kibana', 'logstash', 'filebeat',
        'sonarqube', 'nexus', 'artifactory', 'harbor',
        'argocd', 'flux', 'spinnaker', 'tekton',
        'minio', 'ceph', 'gluster', 'nfs',
        'cockroach', 'cassandra', 'influxdb', 'timescaledb',
        'neo4j', 'arangodb', 'rethinkdb', 'couchdb',
        'memcached', 'varnish', 'squid', 'envoy',
        'linkerd', 'jaeger', 'zipkin', 'opentelemetry',
        'fluentd', 'fluentbit', 'vector', 'telegraf',
        'loki', 'tempo', 'mimir', 'thanos',
        'crossplane', 'backstage', 'portainer', 'rancher',
        'longhorn', 'rook', 'openebs', 'local-path',
        'cert-manager', 'external-dns', 'ingress-nginx',
        'metallb', 'calico', 'cilium', 'weave',
        'flannel', 'canal', 'antrea', 'kube-router',
        'velero', 'restic', 'kopia', 'duplicati',
        'hashicorp', 'boundary', 'nomad', 'packer',
        'waypoint', 'hcl', 'vagrant', 'consul-template',
        'envconsul', 'fabio', 'registrator', 'confd',
        'dnsmasq', 'coredns', 'unbound', 'bind',
        'powerdns', 'route53', 'cloudflare', 'akamai',
        'fastly', 'cloudfront', 'keycdn', 'bunnycdn',
        'stackpath', 'edgio', 'imperva', 'sucuri',
        'waf', 'firewall', 'ids', 'ips', 'siem',
        'soc', 'cert', 'csirt', 'irt', 'abuse',
        'noc', 'ops', 'sre', 'devops', 'platform',
        'infra', 'infrastructure', 'network', 'net',
        'dns', 'dhcp', 'ntp', 'ldap', 'radius',
        'tacacs', 'kerberos', 'sso', 'saml', 'oidc',
        'oauth', 'openid', 'jwt', 'token', 'session',
        'cookie', 'cache', 'session-store', 'redis-sentinel',
        'redis-cluster', 'mongodb-atlas', 'aurora', 'rds',
        'dynamodb', 's3', 'ec2', 'lambda', 'ecs', 'eks',
        'fargate', 'lightsail', 'workspaces', 'connect',
        'chime', 'lex', 'polly', 'rekognition', 'comprehend',
        'translate', 'transcribe', 'textract', 'forecast',
        'personalize', 'fraud-detector', 'detective',
        'guardduty', 'inspector', 'macie', 'security-hub',
        'artifact', 'audit-manager', 'config', 'cloudtrail',
        'cloudwatch', 'x-ray', 'service-catalog', 'systems-manager',
        'parameter-store', 'secrets-manager', 'kms', 'hsm',
        'waf-regional', 'shield', 'route53-resolver',
        'global-accelerator', 'direct-connect', 'transit-gateway',
        'private-link', 'endpoint', 'interface-endpoint',
        'gateway-endpoint', 'nat-gateway', 'internet-gateway',
        'egress-only-gateway', 'customer-gateway', 'virtual-gateway',
        'vpn-gateway', 'site-to-site', 'client-vpn', 'worklink',
        'appstream', 'workdocs', 'workmail', 'ses', 'sns', 'sqs',
        'mq', 'eventbridge', 'step-functions', 'swf', 'simpledb',
        'glacier', 'storage-gateway', 'datasync', 'migration-hub',
        'dms', 'schema-conversion-tool', 'database-migration',
        'elasticache', 'memorydb', 'keyspaces', 'neptune',
        'documentdb', 'qldb', 'timestream', 'managed-blockchain',
        'quantum-ledger', 'ground-station', 'iot', 'greengrass',
        'freertos', 'device-defender', 'device-management',
        'analytics', 'events', 'things-graph', '1-click',
        'robomaker', 'braket', 'panorama', 'lookout',
        'monitron', 'healthlake', 'omics', 'devops-guru',
        'codeartifact', 'codebuild', 'codecommit', 'codedeploy',
        'codepipeline', 'codestar', 'cloud9', 'cloudshell',
        'cloudformation', 'opsworks', 'elastic-beanstalk',
        'lightsail-containers', 'apprunner', 'proton', 'nimble',
        'gamelift', 'lumberyard', 'quicksight', 'athena',
        'emr', 'redshift', 'kinesis', 'msk', 'glue',
        'lake-formation', 'data-pipeline', 'dataprep',
        'clean-rooms', 'data-exchange', 'datazone', 'fin-space',
        'supply-chain', 'iot-twinmaker', 'iot-fleetwise',
        'iot-roborunner', 'iot-sitewise', 'iot-events',
        'iot-jobs', 'iot-wireless', 'iot-core', 'iot-device-tester',
        'sagemaker', 'bedrock', 'q', 'codewhisperer', 'codecatalyst',
        'partyrock', 'builder-id', 'iam-identity-center',
        'single-sign-on', 'directory-service', 'cognito',
        'verified-access', 'private-certificate-authority',
        'certificate-manager', 'signer', 'cloudhsm',
        'payment-cryptography', 'clean-rooms', 'audit-manager',
        'control-tower', 'organizations', 'service-management-portal',
        'marketplace', 'partner-network', 'activate', 'credits',
        'educate', 'startups', 'nonprofits', 'govcloud',
        'china', 'beijing', 'ningxia', 'hybrid', 'outposts',
        'wavelength', 'local-zones', 'snow', 'snowcone',
        'snowball', 'snowmobile', 'transfer-family', 'elemental',
        'mediaconnect', 'mediaconvert', 'medialive', 'mediapackage',
        'mediastore', 'mediatailor', 'interactive-video',
        'nimble-studio', 'end-user-computing', 'appflow',
        'managed-airflow', 'managed-workflows', 'stepfunctions',
        'amazon-managed-grafana', 'amazon-managed-prometheus',
        'amazon-managed-service', 'managed-streaming',
        'managed-blockchain-query', 'managed-ledger',
        'verified-permissions', 'verified-access-endpoints',
        'network-firewall', 'network-manager', 'network-monitor',
        'cloud-map', 'service-discovery', 'app-mesh',
        'cloud-control-api', 'resource-groups', 'tag-editor',
        'trusted-advisor', 'support-center', 'personal-health-dashboard',
        'well-architected-tool', 'migration-evaluator',
        'application-discovery', 'migration-planner',
        'application-migration', 'server-migration',
        'database-migration-service', 'schema-conversion',
        'data-sync', 'transfer', 'family', 'fsx',
        'windows-file-server', 'lustre', 'ontap', 'openzfs',
        'netapp-ontap', 'efs', 's3-express', 's3-glacier',
        's3-intelligent-tiering', 's3-one-zone', 's3-standard',
        's3-infrequent-access', 's3-archive', 's3-deep-archive',
        's3-object-lambda', 's3-multi-region', 's3-cross-region',
        's3-replication', 's3-versioning', 's3-encryption',
        's3-access-points', 's3-batch-operations', 's3-inventory',
        's3-analytics', 's3-storage-lens', 's3-select',
        's3-website', 's3-static-hosting', 's3-cloudfront',
        's3-transfer-acceleration', 's3-presigned-url',
        's3-signed-cookie', 's3-origin-access-identity',
        's3-origin-access-control', 's3-field-level-encryption',
        's3-real-time-logs', 's3-standard-infrequent-access',
        's3-one-zone-infrequent-access', 's3-glacier-instant-retrieval',
        's3-glacier-flexible-retrieval', 's3-glacier-deep-archive',
        's3-object-lock', 's3-compliance-mode', 's3-governance-mode',
        's3-retention-period', 's3-legal-hold', 's3-event-notifications',
        's3-lifecycle-policy', 's3-cross-account', 's3-access-logs',
        's3-requester-pays', 's3-mfa-delete', 's3-block-public-access',
        's3-account-level', 's3-bucket-level', 's3-object-level',
        's3-default-encryption', 's3-bucket-key', 's3-sse-s3',
        's3-sse-kms', 's3-sse-c', 's3-client-side-encryption',
        's3-server-side-encryption', 's3-encryption-context',
        's3-data-protection', 's3-security', 's3-compliance',
        's3-audit', 's3-monitoring', 's3-alerts', 's3-metrics',
        's3-cloudwatch-metrics', 's3-request-metrics',
        's3-storage-metrics', 's3-replication-metrics',
        's3-transfer-acceleration-metrics', 's3-byte-count',
        's3-object-count', 's3-bucket-size', 's3-storage-class',
        's3-age-of-object', 's3-days-to-threshold',
        's3-pending-replication', 's3-failed-replication',
        's3-replication-latency', 's3-operation-metrics',
        's3-get-requests', 's3-put-requests', 's3-delete-requests',
        's3-list-requests', 's3-head-requests', 's3-post-requests',
        's3-select-requests', 's3-errors', 's3-4xx-errors',
        's3-5xx-errors', 's3-first-byte-latency',
        's3-total-request-latency', 's3-time-to-first-byte',
        's3-download-speed', 's3-upload-speed', 's3-throughput',
        's3-bandwidth', 's3-connections', 's3-active-connections',
        's3-new-connections', 's3-closed-connections',
        's3-reset-connections', 's3-timeout-connections',
        's3-failed-connections', 's3-rejected-connections',
        's3-throttled-requests', 's3-rate-limited-requests',
        's3-quota-exceeded', 's3-insufficient-capacity',
        's3-service-unavailable', 's3-slow-down', 's3-too-many-requests',
        's3-bad-request', 's3-forbidden', 's3-not-found',
        's3-method-not-allowed', 's3-conflict', 's3-precondition-failed',
        's3-request-range-not-satisfiable', 's3-unprocessable-entity',
        's3-internal-error', 's3-not-implemented', 's3-bad-gateway',
        's3-service-temporarily-unavailable', 's3-gateway-timeout'
    ]
    
    # 根据大小选择字典
    if wordlist_size == 'large':
        # 可以加载外部字典文件
        wordlist_path = os.path.join(os.path.dirname(__file__), 'wordlists', 'subdomains.txt')
        if os.path.exists(wordlist_path):
            with open(wordlist_path, 'r', encoding='utf-8') as f:
                common_subdomains = [line.strip() for line in f if line.strip()]
    
    log(f"   [INFO] 使用 {len(common_subdomains)} 个常见子域名进行爆破")
    
    found_subdomains = []
    import requests
    
    # 批量测试（每次10个并发）
    batch_size = 10
    for i in range(0, len(common_subdomains), batch_size):
        batch = common_subdomains[i:i+batch_size]
        
        import concurrent.futures
        
        def test_subdomain(sub):
            full_domain = f"{sub}.{domain}"
            try:
                # 尝试HTTP和HTTPS
                for protocol in ['https', 'http']:
                    url = f"{protocol}://{full_domain}"
                    resp = requests.get(url, timeout=3, allow_redirects=False)
                    if resp.status_code in [200, 301, 302, 403, 401]:
                        return full_domain
            except:
                pass
            return None
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=batch_size) as executor:
            futures = [executor.submit(test_subdomain, sub) for sub in batch]
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    found_subdomains.append(result)
                    log(f"   [FOUND] {result}", end='\r')
        
        if (i + batch_size) % 100 == 0:
            log(f"   [PROGRESS] 已测试 {min(i + batch_size, len(common_subdomains))}/{len(common_subdomains)} 个子域名...")
    
    log(f"\n[OK] 暴力破解完成，发现 {len(found_subdomains)} 个活跃子域名")
    
    # 保存结果
    output_file = os.path.join(output_dir, 'brute_subdomains.txt')
    with open(output_file, 'w', encoding='utf-8') as f:
        for sub in sorted(found_subdomains):
            f.write(sub + '\n')
    
    return found_subdomains

def verify_subdomains(subdomains, output_dir):
    """验证子域名是否存活"""
    log("[VERIFY] 验证子域名存活状态...")
    
    import requests
    
    alive_subdomains = []
    
    # 限制验证数量，避免过长时间
    max_verify = min(len(subdomains), 50)  # 最多验证50个
    if len(subdomains) > max_verify:
        log(f"   [INFO] 子域名数量较多({len(subdomains)})，仅验证前{max_verify}个")
        subdomains_to_verify = subdomains[:max_verify]
    else:
        subdomains_to_verify = subdomains
    
    for idx, subdomain in enumerate(subdomains_to_verify, 1):
        if idx % 10 == 0:
            log(f"   [PROGRESS] 已验证 {idx}/{len(subdomains_to_verify)} 个子域名...")
        
        for protocol in ['https', 'http']:
            url = f"{protocol}://{subdomain}"
            try:
                resp = requests.get(url, timeout=3, allow_redirects=True)  # 减少超时时间到3秒
                if resp.status_code in [200, 301, 302, 403, 401, 500]:
                    alive_subdomains.append({
                        'domain': subdomain,
                        'url': url,
                        'status': resp.status_code,
                        'title': resp.text[:200] if resp.text else ''
                    })
                    log(f"   [ALIVE] {url} ({resp.status_code})")
                    break
            except:
                continue
    
    # 保存存活子域名
    output_file = os.path.join(output_dir, 'alive_subdomains.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(alive_subdomains, f, indent=2, ensure_ascii=False)
    
    log(f"[OK] 验证完成，{len(alive_subdomains)} 个子域名存活")
    
    return alive_subdomains

def merge_with_existing_urls(alive_subdomains, existing_urls_file, output_dir):
    """将子域名与现有URL合并"""
    log("[MERGE] 合并子域名到URL列表...")
    
    # 读取现有URL
    existing_urls = []
    if os.path.exists(existing_urls_file):
        with open(existing_urls_file, 'r', encoding='utf-8') as f:
            existing_urls = [line.strip() for line in f if line.strip()]
    
    log(f"   [INFO] 现有URL数量: {len(existing_urls)}")
    
    # 添加子域名根URL
    new_urls = set(existing_urls)
    for sub in alive_subdomains:
        new_urls.add(sub['url'])
    
    # 排序并保存
    final_urls = sorted(list(new_urls))
    
    with open(existing_urls_file, 'w', encoding='utf-8') as f:
        for url in final_urls:
            f.write(url + '\n')
    
    added_count = len(final_urls) - len(existing_urls)
    log(f"[OK] 合并完成，新增 {added_count} 个子域名URL")
    log(f"   [TOTAL] 总URL数量: {len(final_urls)}")
    
    return final_urls

def enumerate_subdomains(target_url, output_dir='.'):
    """主函数：完整的子域名枚举流程"""
    log(f"\n{'='*60}")
    log(f"子域名枚举开始")
    log(f"{'='*60}\n")
    
    # 提取主域名
    domain = extract_domain(target_url)
    log(f"[TARGET] 目标域名: {domain}")
    log(f"[DIR] 输出目录: {output_dir}\n")
    
    all_subdomains = set()
    
    try:
        # 方法1: Subfinder（被动枚举）- 快速，通常几秒到几十秒
        log("[STEP 1/2] 使用 Subfinder 进行被动枚举...")
        subfinder_results = run_subfinder(domain, output_dir)
        all_subdomains.update(subfinder_results)
        log(f"   [INFO] Subfinder 发现 {len(subfinder_results)} 个子域名\n")
        
        # 方法2: Amass（如果可用）- 也很快
        log("[STEP 2/2] 尝试使用 Amass...")
        amass_results = run_amass(domain, output_dir)
        all_subdomains.update(amass_results)
        log(f"   [INFO] Amass 发现 {len(amass_results)} 个子域名\n")
        
        # 注意：暴力破解已禁用，因为耗时太长
        # 如果需要，可以手动启用
        
    except Exception as e:
        log(f"[ERROR] 子域名枚举过程中出错: {e}")
        import traceback
        log(traceback.format_exc())
    
    log(f"\n[SUMMARY] 总共发现 {len(all_subdomains)} 个唯一子域名")
    
    if not all_subdomains:
        log("[WARN] 未发现任何子域名，跳过后续步骤")
        return []
    
    # 显示所有发现的子域名
    log("\n[RESULTS] 发现的子域名列表:")
    for i, sub in enumerate(sorted(all_subdomains)[:20], 1):  # 只显示前20个
        log(f"   {i}. {sub}")
    if len(all_subdomains) > 20:
        log(f"   ... 还有 {len(all_subdomains) - 20} 个")
    
    # 保存原始子域名列表
    raw_file = os.path.join(output_dir, 'all_subdomains.txt')
    with open(raw_file, 'w', encoding='utf-8') as f:
        for sub in sorted(all_subdomains):
            f.write(sub + '\n')
    
    # 验证子域名存活（可能会比较慢）
    try:
        log("\n[VERIFY] 开始验证子域名存活状态...")
        alive_subdomains = verify_subdomains(list(all_subdomains), output_dir)
        
        # 合并到现有URL列表
        existing_urls_file = os.path.join(output_dir, 'all_urls.txt')
        if alive_subdomains:
            merge_with_existing_urls(alive_subdomains, existing_urls_file, output_dir)
    except Exception as e:
        log(f"[WARN] 验证子域名时出错: {e}")
        log("[INFO] 将继续执行后续扫描步骤")
    
    log(f"\n{'='*60}")
    log(f"子域名枚举完成")
    log(f"{'='*60}\n")
    
    return list(all_subdomains)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python subdomain_enum.py <目标URL> [输出目录]")
        print("\n示例:")
        print("  python subdomain_enum.py https://www.anthropic.com ./anthropic_bounty")
        sys.exit(1)
    
    target = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else '.'
    
    enumerate_subdomains(target, output_dir)
