#!/bin/bash
# w69: 真实 curl 测试 - 只带 token
TOKEN='eyJhbGciOiJSUzI1NiIsImtpZCI6IjI0N2Y4MDYwMDM5YjVmNDBkOTQ5NjkzOGJiMTg5NzA2ZWY4ODkzM2QiLCJ0eXAiOiJKV1QifQ.eyJuYW1lIjoiYm9ibyBsaSIsInBpY3R1cmUiOiJodHRwczovL2xoMy5nb29nbGV1c2VyY29udGVudC5jb20vYS9BQ2c4b2NKNXZwOTU1bzJLeUxEZk5QTW01aFdLVmdybmhDSmdTa0ZhVmd5VDhUTUYwUE0xalE9czk2LWMiLCJzdWJzY3JpcHRpb25fdHlwZSI6ImZyZWUiLCJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20vY29tZnl3ZWItYzMxYmUiLCJhdWQiOiJjb21meXdlYi1jMzFiZSIsImF1dGhfdGltZSI6MTc4ODgzNjQ4NiwidXNlcl9pZCI6ImxSUEN4WnAyZXlaaU8yMHJmUGU1bGJUM1c1UyIsInN1YiI6ImxSUEN4WnAyZXlaaU8yMHJmUGU1bGJUM1c1UyIsImlhdCI6MTc4ODgzNjQ4OSwiZXhwIjoxNzg4ODQwMDg5LCJlbWFpbCI6ImxpYm9ibzEyMjlAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImZpcmViYXNlIjp7ImlkZW50aXRpZXMiOnsiZ29vZ2xlLmNvbSI6WyIxMDcxNTU4MjMyOTE4MTE1MDM0NDUiXSwiZW1haWwiOlsibGlib2JvMTIyOUBnbWFpbC5jb20iXX0sInNpZ25faW5fcHJvdmlkZXIiOiJnb29nbGUuY29tIn19.SwE3gVNtymB6dJkPZGX_0Rnl0bm9HDHlYHVfC9y8mFFFy0FqtMwhrZdbc85ZSbCY4tRLgwVdGNbaS5PBeTdiwy_RImtJKpzvqf03sCRmXo81y4H2K41TUqpiN7rR9tmjDN7M6_yjgrqnXOHCn9mrJL5ueBd05IMnsLzjS00OdAofh8ZE18urnTCOajP1AfCsC5zac9x1Ko7payHBh8_6TyZYJwhlqnfurdoVYQpQTnLw8JTzsww942Y2wc6hgi7CXvlidWv9hZm-UhCvjuW8g8fCiUWiRqN3QJm_0cFHqOytCjjIv3V_KL6Up0Ez9EI74s05HrevbgLoSkEsSPJrWA'
echo "=== A. 只 token, 无 cookie ==="
curl -s -o /dev/null -w "HTTP %{http_code}\n" 'https://api.weavy.ai/api/v1/users' \
  -H "authorization: Bearer $TOKEN" \
  -H 'x-weavy-auth-provider: firebase' -H 'x-app-version: 4.1.1214' -H 'x-wv-tier-cookie: 1' \
  -H 'origin: https://app.weavy.ai' \
  -H 'user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36 Edg/149.0.0.0'
echo "=== B. token + 完整最新 cookie (从 w68 提取) ==="
COOKIE=$(head -2 /d/scan/figma_report/_w68_creds.txt | tail -1)
curl -s -o /dev/null -w "HTTP %{http_code}\n" 'https://api.weavy.ai/api/v1/users' \
  -H "authorization: Bearer $TOKEN" \
  -H "cookie: $COOKIE" \
  -H 'x-weavy-auth-provider: firebase' -H 'x-app-version: 4.1.1214' -H 'x-wv-tier-cookie: 1' \
  -H 'origin: https://app.weavy.ai' \
  -H 'user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36 Edg/149.0.0.0'
echo "DONE"
