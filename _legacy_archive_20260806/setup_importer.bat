@echo off
REM 本地資料匯入系統 - Windows快速設置腳本

echo ==================================
echo 🎨 本地資料匯入系統 - 快速設置
echo ==================================
echo.

REM 檢查Python
echo 📋 檢查環境...
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ 錯誤: 未找到 Python
    echo 請先安裝 Python 3.8 或更高版本
    echo 下載地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python 版本: %PYTHON_VERSION%
echo.

REM 安裝依賴
echo 📦 安裝Python套件...
echo.

echo 安裝基礎套件...
python -m pip install -q neo4j chromadb requests flask werkzeug

echo 安裝PDF處理套件...
python -m pip install -q PyPDF2 pdfplumber

echo.
echo ✅ 套件安裝完成
echo.

REM 檢查Docker服務
echo 🔍 檢查資料庫服務...

docker ps 2>nul | findstr "neo4j" >nul
if %ERRORLEVEL% EQU 0 (
    echo ✅ Neo4j 正在運行
) else (
    echo ⚠️  警告: Neo4j 未運行
    echo    請執行: docker-compose up -d
)

REM 檢查ChromaDB
curl -s http://localhost:8001/api/v1/heartbeat >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✅ ChromaDB 正在運行
) else (
    echo ⚠️  警告: ChromaDB 未運行
    echo    請執行: docker-compose up -d
)

REM 檢查Ollama
curl -s http://localhost:11434/api/version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✅ Ollama 正在運行
) else (
    echo ⚠️  警告: Ollama 未運行
    echo    向量嵌入功能可能無法使用
)

echo.

REM 建立範例模板
echo 📝 建立範例模板...
python import_local_data.py --create-template

echo.
echo ✅ 範例模板已建立在: .\import_templates\
echo.

REM 建立測試資料夾
echo 📁 建立測試資料夾...
if not exist "local_import_data" mkdir local_import_data
echo ✅ 測試資料夾: .\local_import_data\
echo.

REM 顯示使用說明
echo ==================================
echo 🎉 設置完成!
echo ==================================
echo.
echo 📚 使用方法:
echo.
echo 1️⃣  命令列介面 (CLI):
echo    python import_local_data.py -f 您的檔案.json
echo    python import_local_data.py -d .\local_import_data\ --recursive
echo.
echo 2️⃣  Web介面:
echo    python web_import_server.py
echo    然後打開瀏覽器: http://localhost:5050
echo.
echo 3️⃣  查看範例:
echo    dir /b .\import_templates\
echo.
echo 📖 完整文檔: .\本地資料匯入完整指南.md
echo.
echo ==================================
echo.

REM 詢問是否啟動Web介面
set /p START_WEB="是否立即啟動Web匯入介面? (y/n): "
if /i "%START_WEB%"=="y" (
    echo.
    echo 🌐 啟動Web介面...
    python web_import_server.py
)

pause
