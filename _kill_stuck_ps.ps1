# Kill the stuck powershell waiting for FilePath input (started from git bash)
$procs = Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" |
    Where-Object { $_.CommandLine -like '*Start-Process*' -and $_.CommandLine -like '*RunAs*' }
foreach ($p in $procs) {
    Write-Host ("killing pid " + $p.ProcessId)
    Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
}
Write-Host "cleanup done"
