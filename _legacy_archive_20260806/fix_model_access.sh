#!/bin/bash

# OpenWebUI 模型訪問修復腳本
# 確保一般使用者可以看到和使用所有模型

echo "=========================================="
echo "OpenWebUI 模型訪問診斷與修復"
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

# 1. 檢查容器狀態
echo -e "${BLUE}步驟 1: 檢查容器狀態${NC}"
echo "=========================================="

if ! docker ps | grep -q art-history-openwebui; then
    echo -e "${RED}❌ OpenWebUI 容器未運行${NC}"
    echo "正在啟動..."
    docker start art-history-openwebui
    sleep 5
fi

if ! docker ps | grep -q art-history-ollama; then
    echo -e "${RED}❌ Ollama 容器未運行${NC}"
    echo "正在啟動..."
    docker start art-history-ollama
    sleep 5
fi

echo -e "${GREEN}✅ 容器運行中${NC}"
echo ""

# 2. 檢查 Ollama 模型
echo -e "${BLUE}步驟 2: 檢查 Ollama 模型列表${NC}"
echo "=========================================="

MODELS=$(curl -s http://localhost:11434/api/tags 2>&1)
if echo "$MODELS" | grep -q "models"; then
    echo -e "${GREEN}✅ Ollama 連接正常${NC}"
    echo ""
    echo "可用模型:"
    echo "$MODELS" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for model in data.get('models', []):
        print(f\"  - {model['name']}\")
except:
    print('  無法解析模型列表')
" 2>/dev/null || echo "$MODELS" | grep -o '"name":"[^"]*"' | cut -d'"' -f4 | sed 's/^/  - /'
else
    echo -e "${RED}❌ Ollama 連接失敗${NC}"
    echo "錯誤訊息: $MODELS"
fi
echo ""

# 3. 檢查模型過濾配置
echo -e "${BLUE}步驟 3: 檢查模型過濾設定${NC}"
echo "=========================================="

MODEL_FILTER=$(docker exec art-history-openwebui env | grep -E "(MODEL_FILTER|ENABLE_MODEL)" 2>&1)
echo "$MODEL_FILTER"

if echo "$MODEL_FILTER" | grep -q "MODEL_FILTER_ENABLED=false"; then
    echo -e "${GREEN}✅ 模型過濾已關閉 (全域共享模式)${NC}"
    echo "   所有使用者應該可以看到所有模型"
else
    echo -e "${YELLOW}⚠️  模型過濾已啟用${NC}"
    echo "   需要為使用者單獨配置模型權限"
fi
echo ""

# 4. 測試 OpenWebUI 到 Ollama 的連接
echo -e "${BLUE}步驟 4: 測試 OpenWebUI → Ollama 連接${NC}"
echo "=========================================="

INTERNAL_TEST=$(docker exec art-history-openwebui curl -s http://art-history-ollama:11434/api/tags 2>&1)
if echo "$INTERNAL_TEST" | grep -q "models"; then
    echo -e "${GREEN}✅ OpenWebUI 可以連接到 Ollama${NC}"
else
    echo -e "${RED}❌ OpenWebUI 無法連接到 Ollama${NC}"
    echo "這可能是網路配置問題"
fi
echo ""

# 5. 檢查 OpenWebUI 日誌中的錯誤
echo -e "${BLUE}步驟 5: 檢查最近的錯誤日誌${NC}"
echo "=========================================="

ERRORS=$(docker logs art-history-openwebui --tail 100 2>&1 | grep -i "error\|fail\|exception" | tail -5)
if [ -n "$ERRORS" ]; then
    echo -e "${YELLOW}⚠️  發現以下錯誤:${NC}"
    echo "$ERRORS"
else
    echo -e "${GREEN}✅ 沒有發現明顯錯誤${NC}"
fi
echo ""

# 6. 修復建議
echo -e "${BLUE}步驟 6: 執行修復操作${NC}"
echo "=========================================="

echo "正在執行以下修復操作:"
echo "1. 重啟 OpenWebUI 容器 (清除快取)"
echo "2. 等待服務完全啟動"
echo ""

read -p "是否繼續? (y/n): " CONFIRM
if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo "操作已取消"
    exit 0
fi

echo ""
echo -e "${YELLOW}重啟 OpenWebUI...${NC}"
docker restart art-history-openwebui

echo "等待服務啟動..."
for i in {1..15}; do
    if curl -s http://localhost:8080/health &>/dev/null; then
        echo -e "${GREEN}✅ OpenWebUI 已就緒${NC}"
        break
    fi
    echo -n "."
    sleep 2
done
echo ""

# 7. 最終驗證
echo ""
echo -e "${BLUE}步驟 7: 最終驗證${NC}"
echo "=========================================="

# 檢查服務健康狀態
HEALTH=$(curl -s http://localhost:8080/health 2>&1)
if echo "$HEALTH" | grep -q "true"; then
    echo -e "${GREEN}✅ OpenWebUI 服務健康${NC}"
else
    echo -e "${RED}❌ OpenWebUI 服務異常${NC}"
fi

# 再次檢查 Ollama 連接
MODELS_AFTER=$(curl -s http://localhost:11434/api/tags 2>&1)
if echo "$MODELS_AFTER" | grep -q "models"; then
    echo -e "${GREEN}✅ Ollama 連接正常${NC}"
else
    echo -e "${RED}❌ Ollama 連接失敗${NC}"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}診斷與修復完成!${NC}"
echo "=========================================="
echo ""
echo -e "${YELLOW}接下來請一般使用者執行以下步驟:${NC}"
echo ""
echo "1. 清除瀏覽器快取:"
echo "   Chrome: Ctrl + Shift + Delete"
echo "   選擇 'All time' 和 'Cached images and files'"
echo "   點擊 'Clear data'"
echo ""
echo "2. 重新訪問 OpenWebUI:"
echo "   http://localhost:8080"
echo ""
echo "3. 登入一般使用者帳號"
echo ""
echo "4. 點擊 '新對話' 並查看模型選擇器"
echo "   應該可以看到:"
echo "   - llama3.1:70b"
echo "   - qwen3:30b"
echo "   - deepseek-r1:32b"
echo "   - 以及其他所有模型"
echo ""
echo -e "${BLUE}如果還是看不到模型,請查看詳細指南:${NC}"
echo "  OpenWebUI模型權限管理指南.md"
echo ""
