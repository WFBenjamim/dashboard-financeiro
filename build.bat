@echo off
setlocal

if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

python -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --onedir ^
    --windowed ^
    --name DashboardFinanceiroDesktop ^
    --collect-all webview ^
    --add-data "app.py;." ^
    --add-data "assets;assets" ^
    --add-data "components;components" ^
    --add-data "config;config" ^
    --add-data "utils;utils" ^
    desktop_app.py

endlocal