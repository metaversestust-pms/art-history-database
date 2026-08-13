#!/bin/bash
# 藝術史資料更新腳本
# 功能：更新資料並驗證 OpenWebUI 自動使用最新資料

echo "🎨 藝術史資料更新工具"
echo "================================"
echo ""

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 1. 檢查 Docker 服務
echo "📊 步驟 1: 檢查必要服務..."
echo "--------------------------------"

SERVICES=("art-history-neo4j" "art-history-chromadb" "art-history-ollama")
ALL_RUNNING=true

for service in "${SERVICES[@]}"; do
    if docker ps --format '{{.Names}}' | grep -q "^${service}$"; then
        echo -e "${GREEN}✅ ${service} 運行中${NC}"
    else
        echo -e "${RED}❌ ${service} 未運行${NC}"
        ALL_RUNNING=false
    fi
done

if [ "$ALL_RUNNING" = false ]; then
    echo ""
    echo -e "${RED}錯誤: 部分服務未運行，請先啟動所有服務${NC}"
    echo "提示: docker-compose up -d"
    exit 1
fi

echo ""

# 2. 記錄更新前的資料量
echo "📈 步驟 2: 記錄當前資料量..."
echo "--------------------------------"

# Neo4j 節點數
NEO4J_BEFORE=$(docker exec art-history-neo4j cypher-shell -u neo4j -p arthistory123 \
    "MATCH (n) RETURN count(n)" --format plain 2>/dev/null | tail -n 1 | tr -d ' ')

if [ -z "$NEO4J_BEFORE" ]; then
    echo -e "${RED}❌ 無法連接 Neo4j${NC}"
    exit 1
fi

echo -e "${BLUE}📊 Neo4j 節點數: ${NEO4J_BEFORE}${NC}"

# ChromaDB 向量數（可選）
# 這需要 jq 工具，如果沒有可以跳過
if command -v jq &> /dev/null; then
    CHROMA_BEFORE=$(curl -s http://localhost:8001/api/v2/tenants/default_tenant/databases/default_database/collections/aa7a55a2-924e-41b0-a0f7-9b5c031477a4 2>/dev/null | jq -r '.count // "N/A"')
    echo -e "${BLUE}📊 ChromaDB 向量數: ${CHROMA_BEFORE}${NC}"
fi

echo ""

# 3. 詢問是否運行爬蟲
echo "🕷️ 步驟 3: 資料爬取"
echo "--------------------------------"
read -p "是否運行爬蟲更新資料？(y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${YELLOW}🕷️ 開始爬取新資料...${NC}"
    echo "這可能需要幾分鐘時間，請耐心等待..."
    echo ""

    # 運行爬蟲（根據您的實際爬蟲腳本調整）
    if [ -f "crawl_renaissance_baroque.py" ]; then
        python3 crawl_renaissance_baroque.py
        CRAWLER_EXIT_CODE=$?

        if [ $CRAWLER_EXIT_CODE -eq 0 ]; then
            echo ""
            echo -e "${GREEN}✅ 爬蟲執行完成${NC}"
        else
            echo ""
            echo -e "${RED}❌ 爬蟲執行失敗（退出碼: $CRAWLER_EXIT_CODE）${NC}"
            exit 1
        fi
    else
        echo -e "${YELLOW}⚠️ 找不到爬蟲腳本，跳過此步驟${NC}"
    fi
else
    echo -e "${YELLOW}⏭️ 跳過爬蟲，僅檢查資料狀態${NC}"
fi

echo ""

# 4. 確認資料已更新
echo "📈 步驟 4: 檢查資料更新..."
echo "--------------------------------"

# 等待幾秒確保資料寫入完成
sleep 2

NEO4J_AFTER=$(docker exec art-history-neo4j cypher-shell -u neo4j -p arthistory123 \
    "MATCH (n) RETURN count(n)" --format plain 2>/dev/null | tail -n 1 | tr -d ' ')

echo -e "${BLUE}📊 Neo4j 節點數: ${NEO4J_AFTER}${NC}"

if command -v jq &> /dev/null; then
    CHROMA_AFTER=$(curl -s http://localhost:8001/api/v2/tenants/default_tenant/databases/default_database/collections/aa7a55a2-924e-41b0-a0f7-9b5c031477a4 2>/dev/null | jq -r '.count // "N/A"')
    echo -e "${BLUE}📊 ChromaDB 向量數: ${CHROMA_AFTER}${NC}"
fi

# 計算差異
if [[ "$NEO4J_BEFORE" =~ ^[0-9]+$ ]] && [[ "$NEO4J_AFTER" =~ ^[0-9]+$ ]]; then
    DIFF=$((NEO4J_AFTER - NEO4J_BEFORE))

    if [ $DIFF -gt 0 ]; then
        echo ""
        echo -e "${GREEN}✨ 新增了 ${DIFF} 個 Neo4j 節點${NC}"
    elif [ $DIFF -lt 0 ]; then
        echo ""
        echo -e "${YELLOW}⚠️ 減少了 ${DIFF#-} 個 Neo4j 節點${NC}"
    else
        echo ""
        echo -e "${YELLOW}ℹ️ Neo4j 節點數量未變化${NC}"
    fi
fi

echo ""

# 5. 資料庫詳細統計
echo "📊 步驟 5: 資料庫詳細統計..."
echo "--------------------------------"

echo "Neo4j 節點類型分佈:"
docker exec art-history-neo4j cypher-shell -u neo4j -p arthistory123 \
    "MATCH (n) RETURN labels(n)[0] as type, count(n) as count ORDER BY count DESC" \
    --format plain 2>/dev/null | head -n 20

echo ""

# 6. 測試提示
echo "🎉 完成！"
echo "================================"
echo ""
echo -e "${GREEN}✅ 資料已更新（或確認為最新狀態）${NC}"
echo ""
echo -e "${BLUE}💡 測試建議：${NC}"
echo ""
echo "1. 訪問 OpenWebUI:"
echo "   http://localhost:8080"
echo ""
echo "2. 選擇任意 LLM+RAG 模型，例如:"
echo "   - llama31-enhanced-rag (最全面)"
echo "   - qwen3-30b-vector-rag (中文優化)"
echo "   - deepseek-32b-advanced-rag (深度分析)"
echo ""
echo "3. 測試問題:"
echo "   ❓ 資料庫中有多少件藝術品？"
echo "   ❓ 文藝復興時期有哪些重要藝術家？"
echo "   ❓ 莫內的睡蓮系列有什麼特色？"
echo ""
echo -e "${GREEN}🎨 系統會自動使用最新資料，無需重新創建模型！${NC}"
echo ""

# 7. 高級選項
echo "================================"
echo "高級選項:"
echo "--------------------------------"
echo "A. 查看完整系統狀態: ./check_system_status.sh"
echo "B. 測試 RAG 服務器: curl http://localhost:8010/health"
echo "C. 查看 Ollama 模型: docker exec art-history-ollama ollama list | grep rag"
echo ""
