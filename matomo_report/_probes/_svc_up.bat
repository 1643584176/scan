@echo off
rem Start matomo local services via schtasks (survives agent console closes)
schtasks /Create /TN "matomoLocalSvc" /TR "F:\scan\.venv\Scripts\python.exe F:\scan\matomo_report\_probes\_start_services.py" /SC ONCE /ST 23:59 /F >NUL 2>&1
schtasks /Run /TN "matomoLocalSvc"
timeout /t 20 /nobreak >NUL
schtasks /Query /TN "matomoLocalSvc" /V /FO LIST | findstr /C:"状态" /C:"Status" /C:"Last Run"
