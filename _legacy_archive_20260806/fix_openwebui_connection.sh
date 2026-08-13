#!/bin/bash
# OpenWebUI 資料庫連接修復腳本
# 自動修復 OpenWebUI 到 ChromaDB 和 Ollama 的連接問題

echo "=========================================="
echo "🔧 OpenWebUI 資料庫連接修復腳本"
echo "=========================================="
echo ""

# 顏色定義
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 步驟 1: 檢查當前連接狀態
echo "📊 步驟 1: 檢查當前連接狀態"
echo "------------------------------------------"

echo -n "檢查 OpenWebUI 容器狀態... "
if docker ps | grep -q art-history-openwebui; then
    echo -e "${GREEN}✅ 運行中${NC}"
else
    echo -e "${RED}❌ 未運行${NC}"
    echo "請先啟動 OpenWebUI 容器"
    exit 1
fi

echo -n "檢查 ChromaDB 容器狀態... "
if docker ps | grep -q art-history-chromadb; then
    echo -e "${GREEN}✅ 運行中${NC}"
else
    echo -e "${RED}❌ 未運行${NC}"
    echo "請先啟動 ChromaDB 容器"
    exit 1
fi

echo -n "檢查 Ollama 容器狀態... "
if docker ps | grep -q art-history-ollama; then
    echo -e "${GREEN}✅ 運行中${NC}"
else
    echo -e "${RED}❌ 未運行${NC}"
    echo "請先啟動 Ollama 容器"
    exit 1
fi

echo ""

# 步驟 2: 測試當前連接
echo "🔍 步驟 2: 測試當前連接"
echo "------------------------------------------"

echo "測試 OpenWebUI → ChromaDB 連接..."
docker exec art-history-openwebui python3 -c "
import chromadb
try:
    # 測試使用原始主機名
    client = chromadb.HttpClient(host='chromadb', port=8000)
    client.list_collections()
    print('✅ 使用 chromadb 主機名: 成功')
    exit(0)
except Exception as e:
    print('❌ 使用 chromadb 主機名: 失敗')

    # 測試使用完整容器名
    try:
        client = chromadb.HttpClient(host='art-history-chromadb', port=8000)
        collections = client.list_collections()
        print(f'✅ 使用 art-history-chromadb: 成功 ({len(collections)} collections)')
        exit(2)
    except Exception as e2:
        print(f'❌ 使用 art-history-chromadb: 失敗 - {e2}')
        exit(1)
" 2>&1

CHROMA_TEST=$?

if [ $CHROMA_TEST -eq 0 ]; then
    echo -e "${GREEN}✅ ChromaDB 連接正常 (使用 chromadb)${NC}"
    NEED_FIX=false
elif [ $CHROMA_TEST -eq 2 ]; then
    echo -e "${YELLOW}⚠️  ChromaDB 連接問題: 需要使用完整容器名 art-history-chromadb${NC}"
    NEED_FIX=true
else
    echo -e "${RED}❌ ChromaDB 連接完全失敗${NC}"
    exit 1
fi

echo ""

# 步驟 3: 提供修復選項
if [ "$NEED_FIX" = true ]; then
    echo "🔧 步驟 3: 修復選項"
    echo "------------------------------------------"
    echo ""
    echo "發現問題: OpenWebUI 無法使用簡化主機名 'chromadb' 連接"
    echo ""
    echo "修復方案:"
    echo "1. [推薦] 修改 OpenWebUI 環境變數 (需要重啟容器)"
    echo "2. [臨時] 在 OpenWebUI 中手動上傳文檔"
    echo "3. [高級] 修改 Docker 網路配置"
    echo ""

    read -p "選擇修復方案 (1/2/3) 或按 q 退出: " choice

    case $choice in
        1)
            echo ""
            echo "📝 方案 1: 修改環境變數"
            echo "------------------------------------------"
            echo ""
            echo "請找到 OpenWebUI 的啟動配置檔案 (docker-compose.yml 或 .env)"
            echo "並修改以下環境變數:"
            echo ""
            echo "  CHROMA_HTTP_HOST=art-history-chromadb  (改為完整容器名)"
            echo "  OLLAMA_BASE_URL=http://art-history-ollama:11434"
            echo ""
            echo "然後執行:"
            echo "  docker-compose restart art-history-openwebui"
            echo ""
            echo "修改完成後，再次執行此腳本驗證連接。"
            ;;
        2)
            echo ""
            echo "📝 方案 2: 手動上傳文檔"
            echo "------------------------------------------"
            echo ""
            echo "1. 打開瀏覽器訪問: http://localhost:8080"
            echo "2. 進入 Workspace > Documents"
            echo "3. 上傳以下檔案:"
            echo "   - 漢寶德校長生平.pdf"
            echo "   - 漢寶德紀念館導覽手冊.pdf"
            echo "   - 認識南藝.pdf"
            echo "   - 20個測試LLM關於漢寶德的測試提問及簡短答案.txt"
            echo "   - 專用字.txt"
            echo "   - 通用字.txt"
            echo "4. 在對話中啟用這些文檔"
            echo ""
            ;;
        3)
            echo ""
            echo "📝 方案 3: Docker 網路配置"
            echo "------------------------------------------"
            echo ""
            echo "這需要修改 docker-compose.yml，添加網路別名:"
            echo ""
            echo "services:"
            echo "  chromadb:"
            echo "    networks:"
            echo "      art-history-network:"
            echo "        aliases:"
            echo "          - chromadb"
            echo "          - art-history-chromadb"
            echo ""
            echo "然後執行: docker-compose down && docker-compose up -d"
            echo ""
            ;;
        q)
            echo "退出"
            exit 0
            ;;
        *)
            echo "無效選擇"
            exit 1
            ;;
    esac
else
    echo "🎉 步驟 3: 連接測試通過"
    echo "------------------------------------------"
    echo -e "${GREEN}✅ 所有連接正常，無需修復${NC}"
    echo ""

    # 顯示資料統計
    echo "📊 資料統計:"
    docker exec art-history-openwebui python3 -c "
import chromadb
client = chromadb.HttpClient(host='chromadb', port=8000)
collections = client.list_collections()
for c in collections:
    print(f'  - {c.name}: {c.count()} documents')
" 2>&1
fi

echo ""
echo "=========================================="
echo "✅ 診斷完成"
echo "=========================================="
