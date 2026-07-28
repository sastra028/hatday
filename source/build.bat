@echo off
chcp 65001 > nul
title HayDay Bot - Auto Build Script
color 0A

echo ========================================================
echo       🚀 Starting Build Process (PyArmor + PyInstaller)
echo ========================================================
echo.

set SOURCE_FILE=main.py

:: 1. ตรวจสอบว่าไฟล์ต้นทางมีอยู่จริงหรือไม่
if not exist %SOURCE_FILE% (
    color 0C
    echo [ERROR] Not found %SOURCE_FILE% in this folder!
    pause
    exit /b
)

:: 2. ลบโฟลเดอร์เก่าออกก่อนเพื่อป้องกันไฟล์ตกค้าง
echo [1/3] Cleaning up old build folders...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist *.spec del /f /q *.spec

:: 3. สั่งเข้ารหัสโค้ดด้วย PyArmor
echo.
echo [2/3] Obfuscating code with PyArmor...
python -m pyarmor.cli gen %SOURCE_FILE%

if %errorlevel% neq 0 (
    color 0C
    echo [ERROR] PyArmor failed! Check Python installation.
    pause
    exit /b
)

:: 4. สั่งแพ็กรวมร่างเป็นไฟล์ .exe ด้วย PyInstaller (ระบุ --add-data "images;images" ตรงๆ)
echo.
echo [3/3] Building single EXE file with PyInstaller...
python -m PyInstaller --onefile ^
    --collect-all pyarmor_runtime_000000 ^
    --add-data "images;images" ^
    --hidden-import=uuid ^
    --hidden-import=requests ^
    --hidden-import=socket ^
    --hidden-import=pyautogui ^
    --hidden-import=cv2 ^
    --hidden-import=numpy ^
    --hidden-import=keyboard ^
    --paths dist ^
    dist\%SOURCE_FILE%

if %errorlevel% neq 0 (
    color 0C
    echo.
    echo [ERROR] PyInstaller failed!
    pause
    exit /b
)

echo.
echo ========================================================
echo       ✅ BUILD SUCCESSFUL!
echo ========================================================
echo.

explorer dist
pause