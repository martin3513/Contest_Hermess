@echo off
chcp 65001 >nul
setlocal
set "PYTHONUTF8=1"
pushd "%~dp0"
where python >nul 2>nul
if errorlevel 1 goto usepy
python start.py
goto done
:usepy
where py >nul 2>nul
if errorlevel 1 goto missing
py -3 start.py
goto done
:missing
echo Python 3.10+ is required. Install Python, then run this file again.
:done
popd
pause
