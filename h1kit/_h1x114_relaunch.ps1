# 杀光 Chrome(含 elevated)后以无痕+调试端口启动
Stop-Process -Name chrome -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 3
Start-Process -FilePath 'C:\Program Files\Google\Chrome\Application\chrome.exe' -ArgumentList '--incognito','--remote-debugging-port=9222','https://hackerone.com'
