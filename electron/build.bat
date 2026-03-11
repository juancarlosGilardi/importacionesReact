@echo off
echo === ImportCost Pro - Build Script ===
echo.

echo [1/4] Building frontend...
cd /d "%~dp0..\frontend"
call npm run build
if errorlevel 1 (
    echo ERROR: Frontend build failed
    exit /b 1
)

echo [2/4] Copying frontend build to electron...
xcopy /s /y /i dist "%~dp0web-dist"

echo [3/4] Installing electron dependencies...
cd /d "%~dp0"
call npm install

echo [4/4] Building Electron app...
call npm run dist

echo.
echo === Build complete! Check electron/dist/ for the installer ===
pause
