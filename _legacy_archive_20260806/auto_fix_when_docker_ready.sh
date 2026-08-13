#!/bin/bash

# 自動等待 Docker 啟動並執行修復腳本

echo "=========================================="
echo "OpenWebUI 自動修復腳本"
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

# 等待 Docker 啟動
echo -e "${YELLOW}⏳ 正在等待 Docker 啟動...${NC}"
echo "請在 Windows 上開啟 Docker Desktop"
echo ""

MAX_WAIT=180  # 最多等待 3 分鐘
WAITED=0

while ! docker ps &>/dev/null; do
    if [ $WAITED -ge $MAX_WAIT ]; then
        echo -e "${RED}❌ 等待超時 (3 分鐘)${NC}"
        echo "請手動啟動 Docker Desktop,然後執行:"
        echo "  bash fix_openwebui_auth.sh"
        exit 1
    fi

    echo -n "."
    sleep 5
    WAITED=$((WAITED + 5))
done

echo ""
echo -e "${GREEN}✅ Docker 已啟動!${NC}"
echo ""

# 執行診斷
echo -e "${BLUE}步驟 1: 執行診斷${NC}"
echo "=========================================="
bash diagnose_openwebui.sh
echo ""

# 詢問是否繼續
echo -e "${YELLOW}是否要執行修復? (y/n): ${NC}"
read -r CONFIRM

if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo -e "${BLUE}操作已取消${NC}"
    echo "您可以稍後手動執行:"
    echo "  bash fix_openwebui_auth.sh"
    exit 0
fi

echo ""
echo -e "${BLUE}步驟 2: 執行修復${NC}"
echo "=========================================="
bash fix_openwebui_auth.sh

echo ""
echo -e "${GREEN}✅ 完成!${NC}"
echo ""
