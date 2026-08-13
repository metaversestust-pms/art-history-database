#!/bin/bash
# 本地資料匯入系統 - 快速設置腳本

set -e  # 遇到錯誤立即停止

echo "=================================="
echo "🎨 本地資料匯入系統 - 快速設置"
echo "=================================="
echo ""

# 檢查Python版本
echo "📋 檢查環境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 錯誤: 未找到 Python3"
    echo "請先安裝 Python 3.8 或更高版本"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✅ Python 版本: $PYTHON_VERSION"

# 安裝依賴
echo ""
echo "📦 安裝Python套件..."
echo ""

# 基礎依賴
echo "安裝基礎套件..."
pip3 install -q neo4j chromadb requests flask werkzeug

# PDF支援
echo "安裝PDF處理套件..."
pip3 install -q PyPDF2 pdfplumber

echo ""
echo "✅ 套件安裝完成"

# 檢查資料庫服務
echo ""
echo "🔍 檢查資料庫服務..."

# 檢查Neo4j
if docker ps | grep -q "neo4j"; then
    echo "✅ Neo4j 正在運行"
else
    echo "⚠️  警告: Neo4j 未運行"
    echo "   請執行: docker-compose up -d"
fi

# 檢查ChromaDB
if curl -s http://localhost:8001/api/v1/heartbeat &> /dev/null; then
    echo "✅ ChromaDB 正在運行"
else
    echo "⚠️  警告: ChromaDB 未運行"
    echo "   請執行: docker-compose up -d"
fi

# 檢查Ollama
if curl -s http://localhost:11434/api/version &> /dev/null; then
    echo "✅ Ollama 正在運行"
else
    echo "⚠️  警告: Ollama 未運行"
    echo "   向量嵌入功能可能無法使用"
fi

# 建立範例模板
echo ""
echo "📝 建立範例模板..."
python3 import_local_data.py --create-template

echo ""
echo "✅ 範例模板已建立在: ./import_templates/"

# 建立測試資料夾
echo ""
echo "📁 建立測試資料夾..."
mkdir -p ./local_import_data
echo "✅ 測試資料夾: ./local_import_data/"

# 顯示使用說明
echo ""
echo "=================================="
echo "🎉 設置完成!"
echo "=================================="
echo ""
echo "📚 使用方法:"
echo ""
echo "1️⃣  命令列介面 (CLI):"
echo "   python3 import_local_data.py -f 您的檔案.json"
echo "   python3 import_local_data.py -d ./local_import_data/ --recursive"
echo ""
echo "2️⃣  Web介面:"
echo "   python3 web_import_server.py"
echo "   然後打開瀏覽器: http://localhost:5050"
echo ""
echo "3️⃣  查看範例:"
echo "   ls -la ./import_templates/"
echo ""
echo "📖 完整文檔: ./本地資料匯入完整指南.md"
echo ""
echo "=================================="

# 詢問是否立即啟動Web介面
echo ""
read -p "是否立即啟動Web匯入介面? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🌐 啟動Web介面..."
    python3 web_import_server.py
fi
