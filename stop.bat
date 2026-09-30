@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
echo ==========================================================
echo   Stopping service listening on port 8004 ...
echo ==========================================================
set "SEEN= "
set "FOUND=0"
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8004" ^| findstr "LISTENING"') do (
    echo !SEEN! | findstr /c:" %%a " >nul
    if errorlevel 1 (
        set "SEEN=!SEEN!%%a "
        set "FOUND=1"
        echo   [STOP] Killing PID %%a ...
        taskkill /F /PID %%a >nul 2>&1
        if errorlevel 1 (
            echo          Failed - maybe already exited
        ) else (
            echo          OK
        )
    )
)
if "!FOUND!"=="0" echo   No process is listening on port 8004.
echo.
echo Verifying port 8004 ...
netstat -ano | findstr ":8004" | findstr "LISTENING" >nul
if errorlevel 1 (
    echo   Port 8004 is now free.
) else (
    echo   Warning: port 8004 is still in use!
)
echo Done.
endlocal
