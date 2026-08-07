"""在页面环境里找 Apollo Client / React store，尝试直接调用 GraphQL"""
import sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    br = p.chromium.launch(channel='msedge', headless=False)
    ctx = br.new_context(viewport={'width': 1440, 'height': 900},
                         user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36')
    page = ctx.new_page()

    def mock_rise(route):
        if 'icprivate.com' in route.request.url:
            route.fulfill(status=200, content_type='application/grpc-web-text', body='AAAAAA==')
        else:
            route.continue_()
    page.route('**/*', mock_rise)

    page.goto('https://www.instacart.com/signup', timeout=60000, wait_until='domcontentloaded')
    page.wait_for_timeout(9000)

    # 探测 window 上的 Apollo/React 实例
    probe = page.evaluate("""() => {
        const out = {};
        // 1. 常见全局名
        const names = ['__APOLLO_CLIENT__', '__APOLLO_STATE__', 'apolloClient', 'ApolloClient', '__STORE__', '__REDUX_STORE__', 'store', '__NEXT_DATA__'];
        for (const n of names) {
            if (window[n]) {
                const v = window[n];
                out[n] = typeof v === 'object' ? 'object:' + (v.constructor ? v.constructor.name : '?') : typeof v;
            }
        }
        // 2. React fiber root
        const root = document.getElementById('root');
        if (root) {
            const fk = Object.keys(root).find(k => k.startsWith('__reactFiber'));
            if (fk) {
                out['reactFiber'] = 'found ' + fk;
                // 从 fiber 向上找 ApolloProvider / client
                let f = root[fk];
                for (let i = 0; i < 40 && f; i++) {
                    const memo = f.memoizedProps;
                    if (memo && (memo.client || memo.apollo)) {
                        out['apolloInFiber'] = 'depth=' + i + ' keys=' + Object.keys(memo).slice(0, 10).join(',');
                        if (memo.client && memo.client.link) {
                            out['apolloClientObj'] = 'link=' + (memo.client.link.constructor ? memo.client.link.constructor.name : '?');
                            // 尝试直接用 client 发请求
                            try {
                                window.__probe_client = memo.client;
                            } catch (e) {}
                        }
                        break;
                    }
                    f = f.return;
                }
            }
        }
        // 3. webpack runtime 的模块缓存（找 graphql 相关）
        out['webpackChunks'] = Object.keys(window).filter(k => k.startsWith('webpack')).length;
        return out;
    }""")
    print('=== 探测结果 ===')
    print(json.dumps(probe, ensure_ascii=False, indent=1))

    # 如果有 client，直接用它发查询（用服务端已注册的 AccountsHeader 验证机制）
    result = page.evaluate("""async () => {
        const c = window.__probe_client;
        if (!c) return 'NO_CLIENT';
        try {
            // 尝试通过 client 的 httpLink 发送任意 mutation（观察服务端是否接受完整 query）
            const resp = await c.query({query: 'query AccountsHeader { viewLayout { id } }'});
            return JSON.stringify(resp).slice(0, 300);
        } catch (e) {
            return 'ERR: ' + (e.message || String(e)).slice(0, 200);
        }
    }""")
    print()
    print('=== client 直调 ===')
    print(result)
    br.close()
