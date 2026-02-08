@echo off
REM Stop TOB Calculator

echo Stopping TOB Calculator...

REM Kill Flask process
taskkill /F /IM python.exe /FI "WINDOWTITLE eq*app.py*" >nul 2>&1

REM Alternative: Kill all Python processes (use with caution)
REM taskkill /F /IM python.exe

echo TOB Calculator stopped.
timeout /t 2
