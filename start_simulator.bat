@echo off
chcp 65001 > nul
title 가상 배기 사운드 시뮬레이터 & 튜닝 콕핏

echo ===================================================================
echo   🚗 가상 배기 사운드 시뮬레이터 (Supercar Exhaust Sound System)
echo   [포르쉐 911 GT3 / 페라리 F8 / 마세라티 GT / 람보르기니 우라칸]
echo ===================================================================
echo.
echo 1단계 PC 시뮬레이터를 실행합니다...
echo.

set PYTHONPATH=
"C:\Program Files\Python313\python.exe" "%~dp0app_gui.py"

pause
