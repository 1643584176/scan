$p = Get-CimInstance Win32_Process -Filter "ProcessId=17392" -ErrorAction SilentlyContinue
if ($p) {
    Write-Output ("PID 17392: " + $p.Name)
    Write-Output ("CMD: " + $p.CommandLine)
} else {
    Write-Output "PID 17392 not found"
}
Write-Output "--- all python ---"
Get-CimInstance Win32_Process -Filter "Name like 'python%'" | ForEach-Object {
    Write-Output ($_.ProcessId.ToString() + " : " + $_.CommandLine)
}
