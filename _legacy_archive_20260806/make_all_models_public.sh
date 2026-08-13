#!/bin/bash

# 將所有 OpenWebUI 模型設為公開
# 讓所有使用者都能看到和使用這些模型

echo "=========================================="
echo "OpenWebUI 模型公開化腳本"
echo "=========================================="
echo ""

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

DB_PATH="/app/backend/data/webui.db"

echo -e "${BLUE}步驟 1: 備份數據庫${NC}"
echo "=========================================="

BACKUP_DIR="./backups"
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/webui-models-backup-$(date +%Y%m%d-%H%M%S).db"

docker cp art-history-openwebui:$DB_PATH "$BACKUP_FILE" 2>/dev/null
if [ -f "$BACKUP_FILE" ]; then
    echo -e "${GREEN}✅ 數據庫已備份至: $BACKUP_FILE${NC}"
else
    echo -e "${YELLOW}⚠️  無法備份數據庫${NC}"
fi
echo ""

echo -e "${BLUE}步驟 2: 檢查當前模型狀態${NC}"
echo "=========================================="

TOTAL_MODELS=$(docker exec art-history-openwebui sqlite3 $DB_PATH "SELECT COUNT(*) FROM model;" 2>&1)
RESTRICTED_MODELS=$(docker exec art-history-openwebui sqlite3 $DB_PATH "SELECT COUNT(*) FROM model WHERE access_control != '{}';" 2>&1)

echo "總模型數: $TOTAL_MODELS"
echo "有訪問限制的模型: $RESTRICTED_MODELS"
echo ""

if [ "$RESTRICTED_MODELS" = "0" ]; then
    echo -e "${GREEN}✅ 所有模型已經是公開的!${NC}"
    echo "無需修改"
    exit 0
fi

echo -e "${BLUE}步驟 3: 更新模型訪問控制${NC}"
echo "=========================================="

echo "將所有模型的 access_control 設為空 (公開訪問)..."

# 更新所有模型,將 access_control 設為空 JSON {}
docker exec art-history-openwebui sqlite3 $DB_PATH <<EOF
UPDATE model SET access_control = '{}' WHERE access_control != '{}';
EOF

RESULT=$?

if [ $RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ 更新成功!${NC}"
else
    echo -e "${RED}❌ 更新失敗!${NC}"
    exit 1
fi
echo ""

echo -e "${BLUE}步驟 4: 驗證更新結果${NC}"
echo "=========================================="

AFTER_RESTRICTED=$(docker exec art-history-openwebui sqlite3 $DB_PATH "SELECT COUNT(*) FROM model WHERE access_control != '{}';" 2>&1)

echo "更新後有訪問限制的模型: $AFTER_RESTRICTED"

if [ "$AFTER_RESTRICTED" = "0" ]; then
    echo -e "${GREEN}✅ 所有模型已設為公開!${NC}"
else
    echo -e "${YELLOW}⚠️  還有 $AFTER_RESTRICTED 個模型有限制${NC}"
fi
echo ""

echo -e "${BLUE}步驟 5: 重啟 OpenWebUI${NC}"
echo "=========================================="

echo "重啟 OpenWebUI 以應用更改..."
docker restart art-history-openwebui

echo "等待服務啟動..."
sleep 15

for i in {1..10}; do
    if curl -s http://localhost:8080/health &>/dev/null; then
        echo -e "${GREEN}✅ OpenWebUI 已就緒${NC}"
        break
    fi
    echo -n "."
    sleep 2
done
echo ""

echo ""
echo "=========================================="
echo -e "${GREEN}✅ 完成!${NC}"
echo "=========================================="
echo ""
echo -e "${YELLOW}下一步操作:${NC}"
echo ""
echo "1. 一般使用者需要:"
echo "   - 登出當前帳號"
echo "   - 清除瀏覽器快取 (Ctrl + Shift + Delete)"
echo "   - 重新登入"
echo "   - 檢查模型選擇器"
echo ""
echo "2. 預期結果:"
echo "   - 一般使用者應該能看到所有 $TOTAL_MODELS 個模型"
echo "   - 包括所有 RAG 模型"
echo ""
echo "3. 測試:"
echo "   以一般使用者登入"
echo "   → 新對話"
echo "   → 點擊模型選擇器"
echo "   → 應該看到完整的模型列表"
echo ""
echo -e "${BLUE}備份位置:${NC} $BACKUP_FILE"
echo ""
