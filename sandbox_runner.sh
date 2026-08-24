#!/bin/bash
# Vercel Sandbox 测试 runner:管理沙箱生命周期并执行命令
TOKEN="vcp_REDACTED_PLACEHOLDER"
TEAM="team_GIy1SZ444lspqeNbh4r8uAUg"
PROJ="prj_iyw2xfjP3RKPT7n8b8c1tBIxxK5F"

NAME="$1"          # 沙箱名
POLICY_JSON="$2"   # networkPolicy JSON
PY_SCRIPT="$3"     # 要执行的 python 脚本文件
TIMEOUT_MS="${4:-120000}"

API="https://api.vercel.com"

# 1. 删除旧沙箱(忽略错误)
curl -s -X DELETE "$API/v2/sandboxes/$NAME?teamId=$TEAM&projectId=$PROJ" -H "Authorization: Bearer $TOKEN" > /dev/null 2>&1

# 2. 创建新沙箱
RESP=$(curl -s -X POST "$API/v2/sandboxes?teamId=$TEAM" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d "{\"projectId\":\"$PROJ\",\"name\":\"$NAME\",\"networkPolicy\":$POLICY_JSON,\"timeout\":1200000}")
SID=$(echo "$RESP" | python -c "import json,sys; print(json.load(sys.stdin).get('session',{}).get('id',''))")
if [ -z "$SID" ]; then echo "FAILED to create sandbox: $RESP" | head -c 400; exit 1; fi
echo "sandbox=$NAME sid=$SID"

# 3. 执行命令(脚本 base64 编码)
PAYLOAD=$(python -c "import base64,pathlib;print(base64.b64encode(pathlib.Path('$PY_SCRIPT').read_bytes()).decode())")
BODY=$(python -c "import json;print(json.dumps({'command':'python3','args':['-u','-c','import base64;exec(base64.b64decode(\"$PAYLOAD\").decode())'],'wait':True,'logs':True,'timeout':$TIMEOUT_MS}))")
echo "$BODY" > ./vs_body.json
curl -s -X POST "$API/v2/sandboxes/sessions/$SID/cmd?teamId=$TEAM" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" --data-binary @./vs_body.json > ./vs_out.jsonl 2>&1
python -c "
import json
for line in open('./vs_out.jsonl', encoding='utf-8'):
    line=line.strip()
    if not line: continue
    try: d=json.loads(line)
    except: continue
    if d.get('stream') in ('stdout','stderr'): print(d.get('data',''),end='')
    elif d.get('stream')=='command': print('EXIT:',d.get('command',{}).get('exitCode'))
"
