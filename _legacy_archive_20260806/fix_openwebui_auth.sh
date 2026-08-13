#!/bin/bash

# OpenWebUI 認證修復腳本
# 解決 401 Unauthorized 和認證配置衝突問題

set -e

echo "=========================================="
echo "OpenWebUI 認證修復腳本"
echo "=========================================="
echo ""

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 專案目錄
PROJECT_DIR="/mnt/c/Users/ssking1999/Desktop/藝術史資料庫/art-history-database"
cd "$PROJECT_DIR"

echo -e "${BLUE}步驟 1: 檢查 Docker 狀態${NC}"
if ! docker ps &>/dev/null; then
    echo -e "${RED}❌ Docker 未運行,請先啟動 Docker Desktop${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker 運行中${NC}"
echo ""

echo -e "${BLUE}步驟 2: 停止 OpenWebUI 容器${NC}"
docker-compose -f docker-compose.openwebui.yml stop openwebui
echo -e "${GREEN}✅ 容器已停止${NC}"
echo ""

echo -e "${BLUE}步驟 3: 備份使用者資料庫${NC}"
BACKUP_DIR="./backups"
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/webui-backup-$(date +%Y%m%d-%H%M%S).db"

if docker ps -a | grep -q art-history-openwebui; then
    docker cp art-history-openwebui:/app/backend/data/webui.db "$BACKUP_FILE" 2>/dev/null || {
        echo -e "${YELLOW}⚠️  無法備份資料庫 (容器可能沒有資料)${NC}"
    }
    if [ -f "$BACKUP_FILE" ]; then
        echo -e "${GREEN}✅ 資料庫已備份至: $BACKUP_FILE${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  容器不存在,跳過備份${NC}"
fi
echo ""

echo -e "${BLUE}步驟 4: 清除舊的容器和快取${NC}"
docker-compose -f docker-compose.openwebui.yml rm -f openwebui
echo -e "${GREEN}✅ 舊容器已清除${NC}"
echo ""

echo -e "${BLUE}步驟 5: 重新啟動 OpenWebUI${NC}"
docker-compose -f docker-compose.openwebui.yml up -d openwebui
echo -e "${GREEN}✅ OpenWebUI 已啟動${NC}"
echo ""

echo -e "${BLUE}步驟 6: 等待服務就緒${NC}"
echo -n "等待 OpenWebUI 啟動"
for i in {1..30}; do
    if docker logs art-history-openwebui 2>&1 | grep -q "Application startup complete" || \
       curl -s http://localhost:8080/health &>/dev/null; then
        echo ""
        echo -e "${GREEN}✅ OpenWebUI 已就緒${NC}"
        break
    fi
    echo -n "."
    sleep 2
done
echo ""

echo -e "${BLUE}步驟 7: 驗證配置${NC}"
echo "當前認證配置:"
docker exec art-history-openwebui env | grep -E "(WEBUI_AUTH|ENABLE_SIGNUP|DEFAULT_USER_ROLE)" || echo "無法讀取配置"
echo ""

echo -e "${BLUE}步驟 8: 檢查資料庫${NC}"
docker exec art-history-openwebui ls -lh /app/backend/data/webui.db 2>/dev/null || echo "資料庫檔案不存在"
echo ""

echo "=========================================="
echo -e "${GREEN}✅ 修復完成!${NC}"
echo "=========================================="
echo ""
echo -e "${YELLOW}下一步操作:${NC}"
echo ""
echo "1. 訪問 OpenWebUI: http://localhost:8080"
echo ""
echo "2. 如果看到登入頁面:"
echo "   - 使用現有帳號登入"
echo "   - 如果忘記密碼,請查看下方的密碼重設說明"
echo ""
echo "3. 如果看到註冊頁面:"
echo "   - 註冊一個新的管理員帳號"
echo "   - 第一個註冊的使用者自動成為管理員"
echo ""
echo "4. 查看日誌 (如果有問題):"
echo "   docker logs art-history-openwebui --tail 100 -f"
echo ""
echo -e "${YELLOW}備份檔案位置:${NC} $BACKUP_FILE"
echo ""
