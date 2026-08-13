#!/bin/bash

# OpenWebUI 診斷腳本
# 檢查當前狀態和問題

echo "=========================================="
echo "OpenWebUI 診斷報告"
echo "=========================================="
echo ""

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 1. Docker 狀態
echo -e "${BLUE}1. Docker 狀態${NC}"
if docker ps &>/dev/null; then
    echo -e "${GREEN}✅ Docker 運行中${NC}"
else
    echo -e "${RED}❌ Docker 未運行${NC}"
    echo "請先啟動 Docker Desktop"
    exit 1
fi
echo ""

# 2. 容器狀態
echo -e "${BLUE}2. OpenWebUI 容器狀態${NC}"
if docker ps | grep -q art-history-openwebui; then
    echo -e "${GREEN}✅ OpenWebUI 容器運行中${NC}"
    docker ps | grep art-history-openwebui
elif docker ps -a | grep -q art-history-openwebui; then
    echo -e "${YELLOW}⚠️  OpenWebUI 容器已停止${NC}"
    docker ps -a | grep art-history-openwebui
else
    echo -e "${RED}❌ OpenWebUI 容器不存在${NC}"
fi
echo ""

# 3. 環境變數
echo -e "${BLUE}3. 認證配置${NC}"
if docker ps | grep -q art-history-openwebui; then
    docker exec art-history-openwebui env | grep -E "(WEBUI_AUTH|ENABLE_SIGNUP|DEFAULT_USER_ROLE)" || echo "無法讀取配置"
else
    echo "容器未運行,無法檢查"
fi
echo ""

# 4. 資料庫狀態
echo -e "${BLUE}4. 資料庫狀態${NC}"
if docker ps | grep -q art-history-openwebui; then
    DB_INFO=$(docker exec art-history-openwebui ls -lh /app/backend/data/webui.db 2>&1)
    if echo "$DB_INFO" | grep -q "webui.db"; then
        echo -e "${GREEN}✅ 資料庫存在${NC}"
        echo "$DB_INFO"

        # 嘗試讀取使用者數量
        USER_COUNT=$(docker exec art-history-openwebui sqlite3 /app/backend/data/webui.db "SELECT COUNT(*) FROM user;" 2>/dev/null || echo "無法讀取")
        echo "使用者數量: $USER_COUNT"
    else
        echo -e "${YELLOW}⚠️  資料庫不存在${NC}"
    fi
else
    echo "容器未運行,無法檢查"
fi
echo ""

# 5. 最近的錯誤日誌
echo -e "${BLUE}5. 最近的錯誤日誌${NC}"
if docker ps | grep -q art-history-openwebui; then
    echo "最後 20 條相關日誌:"
    docker logs art-history-openwebui --tail 100 2>&1 | grep -i -E "(error|401|unauthorized|auth)" | tail -20
    if [ $? -ne 0 ]; then
        echo "未發現錯誤"
    fi
else
    echo "容器未運行,無法檢查日誌"
fi
echo ""

# 6. 網路連接測試
echo -e "${BLUE}6. 網路連接測試${NC}"
if curl -s http://localhost:8080/health &>/dev/null; then
    echo -e "${GREEN}✅ OpenWebUI 可訪問 (http://localhost:8080)${NC}"
elif curl -s http://localhost:8080 &>/dev/null; then
    echo -e "${YELLOW}⚠️  OpenWebUI 可訪問但 health 端點無回應${NC}"
else
    echo -e "${RED}❌ 無法連接到 OpenWebUI (http://localhost:8080)${NC}"
fi
echo ""

# 7. 相關服務
echo -e "${BLUE}7. 相關服務狀態${NC}"
echo "Ollama:"
if docker ps | grep -q art-history-ollama; then
    echo -e "${GREEN}✅ 運行中${NC}"
else
    echo -e "${RED}❌ 未運行${NC}"
fi

echo "ChromaDB:"
if docker ps | grep -q art-history-chromadb; then
    echo -e "${GREEN}✅ 運行中${NC}"
else
    echo -e "${RED}❌ 未運行${NC}"
fi
echo ""

# 8. 診斷總結
echo "=========================================="
echo -e "${BLUE}診斷總結${NC}"
echo "=========================================="
echo ""

if docker ps | grep -q art-history-openwebui; then
    AUTH_STATUS=$(docker exec art-history-openwebui env | grep "WEBUI_AUTH=" | cut -d'=' -f2)

    if [ "$AUTH_STATUS" = "true" ]; then
        echo -e "${YELLOW}問題可能原因:${NC}"
        echo "1. 認證已啟用 (WEBUI_AUTH=true)"
        echo "2. 系統中已有使用者存在"
        echo "3. Session 失效導致 401 錯誤"
        echo ""
        echo -e "${GREEN}建議解決方案:${NC}"
        echo "執行修復腳本:"
        echo "  bash fix_openwebui_auth.sh"
    fi
else
    echo -e "${RED}容器未運行,請先啟動 Docker 和容器${NC}"
fi
echo ""
