#!/bin/bash

# OpenWebUI 完全重置腳本
# ⚠️  警告: 這會刪除所有使用者資料和對話記錄

set -e

echo "=========================================="
echo "OpenWebUI 完全重置腳本"
echo "=========================================="
echo ""

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_DIR="/mnt/c/Users/ssking1999/Desktop/藝術史資料庫/art-history-database"
cd "$PROJECT_DIR"

echo -e "${RED}⚠️  警告: 此操作將:${NC}"
echo "   - 刪除所有使用者帳號"
echo "   - 刪除所有對話記錄"
echo "   - 刪除所有上傳的文件"
echo "   - 重置為全新安裝"
echo ""
echo -e "${YELLOW}請確認您要繼續 (輸入 YES 繼續): ${NC}"
read -r CONFIRM

if [ "$CONFIRM" != "YES" ]; then
    echo -e "${BLUE}操作已取消${NC}"
    exit 0
fi

echo ""
echo -e "${BLUE}步驟 1: 檢查 Docker 狀態${NC}"
if ! docker ps &>/dev/null; then
    echo -e "${RED}❌ Docker 未運行${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker 運行中${NC}"
echo ""

echo -e "${BLUE}步驟 2: 備份現有資料 (以防萬一)${NC}"
BACKUP_DIR="./backups"
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/complete-backup-$(date +%Y%m%d-%H%M%S).tar.gz"

if docker ps -a | grep -q art-history-openwebui; then
    docker cp art-history-openwebui:/app/backend/data ./temp-backup 2>/dev/null || true
    if [ -d "./temp-backup" ]; then
        tar -czf "$BACKUP_FILE" ./temp-backup
        rm -rf ./temp-backup
        echo -e "${GREEN}✅ 備份完成: $BACKUP_FILE${NC}"
    fi
fi
echo ""

echo -e "${BLUE}步驟 3: 停止並移除容器${NC}"
docker-compose -f docker-compose.openwebui.yml down openwebui
echo -e "${GREEN}✅ 容器已停止${NC}"
echo ""

echo -e "${BLUE}步驟 4: 刪除資料卷${NC}"
docker volume rm openwebui_data 2>/dev/null || echo "資料卷不存在或已刪除"
echo -e "${GREEN}✅ 資料卷已刪除${NC}"
echo ""

echo -e "${BLUE}步驟 5: 清理配置目錄${NC}"
if [ -d "./openwebui-config" ]; then
    mv ./openwebui-config "./openwebui-config-backup-$(date +%Y%m%d-%H%M%S)" 2>/dev/null || true
    echo -e "${GREEN}✅ 配置目錄已備份${NC}"
fi
echo ""

echo -e "${BLUE}步驟 6: 重新建立乾淨的環境${NC}"
docker-compose -f docker-compose.openwebui.yml up -d openwebui
echo -e "${GREEN}✅ 新容器已啟動${NC}"
echo ""

echo -e "${BLUE}步驟 7: 等待服務就緒${NC}"
echo -n "等待 OpenWebUI 啟動"
for i in {1..40}; do
    if curl -s http://localhost:8080/health &>/dev/null; then
        echo ""
        echo -e "${GREEN}✅ OpenWebUI 已就緒${NC}"
        break
    fi
    echo -n "."
    sleep 2
done
echo ""

echo "=========================================="
echo -e "${GREEN}✅ 重置完成!${NC}"
echo "=========================================="
echo ""
echo -e "${YELLOW}下一步:${NC}"
echo ""
echo "1. 訪問: http://localhost:8080"
echo ""
echo "2. 建立第一個管理員帳號:"
echo "   - 點擊 'Sign Up'"
echo "   - 填寫管理員資訊"
echo "   - 第一個註冊的使用者自動成為管理員"
echo ""
echo "3. 當前認證配置:"
echo "   - WEBUI_AUTH=true (需要登入)"
echo "   - ENABLE_SIGNUP=true (可以註冊)"
echo "   - DEFAULT_USER_ROLE=pending (新使用者需審核)"
echo ""
echo -e "${BLUE}備份檔案:${NC} $BACKUP_FILE"
echo ""
