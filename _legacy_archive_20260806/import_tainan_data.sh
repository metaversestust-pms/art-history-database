#!/bin/bash
# 南藝大及漢寶德校長資料匯入腳本
# 自動修正 ChromaDB 端口配置並執行匯入

echo "=================================================="
echo "南藝大及漢寶德校長資料匯入工具"
echo "=================================================="
echo ""

# 設定資料目錄
DATA_DIR="./南藝大及漢寶德校長資料整理"

# 檢查資料目錄是否存在
if [ ! -d "$DATA_DIR" ]; then
    echo "❌ 錯誤: 找不到資料目錄 $DATA_DIR"
    exit 1
fi

echo "✅ 找到資料目錄: $DATA_DIR"
echo ""

# 顯示資料夾內容
echo "📁 資料夾內容:"
ls -lh "$DATA_DIR"
echo ""

# 檢查必要的容器是否運行
echo "🔍 檢查系統狀態..."
echo ""

# 檢查 Neo4j
if docker ps | grep -q "art-history-neo4j.*Up"; then
    echo "✅ Neo4j 運行中"
else
    echo "❌ Neo4j 未運行"
    echo "   請先啟動: docker-compose up -d neo4j"
    exit 1
fi

# 檢查 ChromaDB
if docker ps | grep -q "art-history-chromadb.*Up"; then
    CHROMADB_PORT=$(docker ps --format "{{.Ports}}" | grep chromadb | grep -oP '0.0.0.0:\K[0-9]+' | head -1)
    echo "✅ ChromaDB 運行中 (端口: $CHROMADB_PORT)"
else
    echo "❌ ChromaDB 未運行"
    echo "   請先啟動: docker-compose up -d chromadb"
    exit 1
fi

# 檢查 Ollama (用於生成嵌入向量)
if docker ps | grep -q "art-history-ollama.*Up"; then
    echo "✅ Ollama 運行中"
else
    echo "⚠️  Ollama 未運行，ChromaDB 匯入可能失敗"
    echo "   建議啟動: docker-compose up -d ollama"
fi

echo ""
echo "=================================================="
echo "開始匯入資料..."
echo "=================================================="
echo ""

# 執行匯入 - 使用正確的 ChromaDB 端口
python3 import_local_data.py \
    -d "$DATA_DIR" \
    --chromadb-port ${CHROMADB_PORT:-8000} \
    --neo4j-password arthistory123 \
    -v

# 檢查結果
if [ $? -eq 0 ]; then
    echo ""
    echo "=================================================="
    echo "✅ 匯入成功完成！"
    echo "=================================================="
    echo ""
    echo "📊 資料已匯入到:"
    echo "   • Neo4j (知識圖譜): bolt://localhost:7687"
    echo "   • ChromaDB (向量搜尋): http://localhost:${CHROMADB_PORT:-8000}"
    echo ""
    echo "💡 後續操作:"
    echo "   1. 訪問 Neo4j Browser: http://localhost:7474"
    echo "   2. 在 OpenWebUI 中使用: http://localhost:8080"
    echo "   3. 查詢範例:"
    echo "      - 問: 漢寶德出生於哪一年？"
    echo "      - 問: 南藝大的創校校長是誰？"
    echo "      - 問: 漢寶德紀念館在哪裡？"
    echo ""
else
    echo ""
    echo "=================================================="
    echo "❌ 匯入過程出現錯誤"
    echo "=================================================="
    echo ""
    echo "請檢查上方的錯誤訊息，常見問題:"
    echo "   1. Python 依賴缺失: pip install -r requirements.txt"
    echo "   2. 資料庫連接失敗: 檢查容器是否正常運行"
    echo "   3. 權限問題: 檢查檔案讀取權限"
    echo ""
    exit 1
fi
