@echo off
title HayDay Bot Runner
color 0A

echo =========================================
echo       Starting Hay Day Python Bot...
echo =========================================
echo.

:: เปลี่ยน Directory ไปยังโฟลเดอร์ที่เก็บไฟล์
cd /d "%~dp0"

:: เรียกใช้งานไฟล์ Python
python main.py

echo.
echo =========================================
echo       Bot Stopped.
echo =========================================
pause