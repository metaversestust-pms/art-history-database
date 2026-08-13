#!/bin/bash

# OpenWebUI 模型同步修復腳本
# 解決管理員和一般使用者都看不到 Ollama RAG 模型的問題

echo "=========================================="
echo "OpenWebUI 模型同步修復腳本"
echo "=========================================="
echo ""

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 步驟 1: 檢查 Ollama 模型
echo -e "${BLUE}步驟 1: 檢查 Ollama 中的模型...${NC}"
echo "=========================================="

if ! docker ps | grep -q art-history-ollama; then
    echo -e "${RED}❌ Ollama 容器未運行${NC}"
    echo "正在啟動..."
    docker start art-history-ollama
    sleep 5
fi

OLLAMA_MODELS=$(docker exec art-history-ollama ollama list 2>/dev/null | grep -v "^NAME" | wc -l)
RAG_MODELS=$(docker exec art-history-ollama ollama list 2>/dev/null | grep -c "rag" || echo "0")

echo -e "${GREEN}✅ Ollama 運行中${NC}"
echo "   總模型數: $OLLAMA_MODELS"
echo "   RAG 模型數: $RAG_MODELS"
echo ""

if [ "$RAG_MODELS" = "0" ]; then
    echo -e "${YELLOW}⚠️  沒有找到 RAG 模型${NC}"
    echo "請先執行 create_all_rag_models.sh 創建模型"
    exit 1
fi

# 步驟 2: 檢查 OpenWebUI 狀態
echo -e "${BLUE}步驟 2: 檢查 OpenWebUI 狀態...${NC}"
echo "=========================================="

if ! docker ps | grep -q art-history-openwebui; then
    echo -e "${RED}❌ OpenWebUI 容器未運行${NC}"
    echo "正在啟動..."
    docker start art-history-openwebui
    sleep 10
fi

echo -e "${GREEN}✅ OpenWebUI 運行中${NC}"
echo ""

# 步驟 3: 檢查 OpenWebUI 模型 API
echo -e "${BLUE}步驟 3: 檢查 OpenWebUI 模型同步狀態...${NC}"
echo "=========================================="

sleep 2
OPENWEBUI_MODELS=$(curl -s http://localhost:8080/api/models 2>&1 | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(len(data.get('data', [])))
except:
    print('0')
" 2>/dev/null || echo "0")

echo "當前 OpenWebUI 中的模型數量: $OPENWEBUI_MODELS"
echo ""

if [ "$OPENWEBUI_MODELS" = "0" ]; then
    echo -e "${RED}❌ OpenWebUI 沒有同步任何模型${NC}"
    echo ""
    echo -e "${YELLOW}問題確認:${NC}"
    echo "  - Ollama 有 $RAG_MODELS 個 RAG 模型 ✅"
    echo "  - OpenWebUI 有 0 個模型 ❌"
    echo "  - 原因: OpenWebUI 沒有連接到 Ollama"
    echo ""
else
    echo -e "${GREEN}✅ OpenWebUI 已有 $OPENWEBUI_MODELS 個模型${NC}"
    echo ""
    echo "模型列表:"
    curl -s http://localhost:8080/api/models 2>&1 | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    models = data.get('data', [])
    for m in models[:10]:
        print(f\"  - {m.get('id', m.get('name', 'unknown'))}\")
    if len(models) > 10:
        print(f\"  ... 還有 {len(models) - 10} 個模型\")
except:
    pass
" 2>/dev/null
    echo ""
fi

# 步驟 4: 測試連接
echo -e "${BLUE}步驟 4: 測試 OpenWebUI 到 Ollama 的連接...${NC}"
echo "=========================================="

CONN_TEST=$(docker exec art-history-openwebui curl -s http://art-history-ollama:11434/api/tags 2>&1 | grep -c "models" || echo "0")

if [ "$CONN_TEST" -gt "0" ]; then
    echo -e "${GREEN}✅ OpenWebUI 可以連接到 Ollama${NC}"
else
    echo -e "${RED}❌ OpenWebUI 無法連接到 Ollama${NC}"
    echo "網路配置可能有問題"
fi
echo ""

# 步驟 5: 檢查環境變數
echo -e "${BLUE}步驟 5: 檢查環境變數配置...${NC}"
echo "=========================================="

docker exec art-history-openwebui env | grep -E "(OLLAMA_BASE_URL|OLLAMA_API_BASE_URL|ENABLE_OLLAMA)" | while read line; do
    echo "  $line"
done
echo ""

# 步驟 6: 執行修復
if [ "$OPENWEBUI_MODELS" = "0" ]; then
    echo -e "${BLUE}步驟 6: 執行修復操作...${NC}"
    echo "=========================================="
    echo ""

    echo "正在重啟 OpenWebUI 以觸發模型同步..."
    docker restart art-history-openwebui

    echo "等待服務啟動..."
    for i in {1..20}; do
        if curl -s http://localhost:8080/health &>/dev/null; then
            echo -e "${GREEN}✅ OpenWebUI 已就緒${NC}"
            break
        fi
        echo -n "."
        sleep 2
    done
    echo ""

    sleep 5

    echo "驗證修復結果..."
    AFTER_MODELS=$(curl -s http://localhost:8080/api/models 2>&1 | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(len(data.get('data', [])))
except:
    print('0')
" 2>/dev/null || echo "0")

    echo "修復後模型數量: $AFTER_MODELS"
    echo ""

    if [ "$AFTER_MODELS" = "0" ]; then
        echo -e "${RED}❌ 自動修復失敗${NC}"
        echo ""
        echo -e "${YELLOW}請手動執行以下步驟:${NC}"
        echo ""
        echo "1. 以管理員身份登入 OpenWebUI:"
        echo "   http://localhost:8080"
        echo ""
        echo "2. 進入 Admin Panel:"
        echo "   右上角選單 → Admin Panel"
        echo ""
        echo "3. 配置 Ollama 連接:"
        echo "   Settings → Connections → Ollama API"
        echo ""
        echo "4. 設定 Ollama Base URL:"
        echo "   http://art-history-ollama:11434"
        echo ""
        echo "5. 驗證連接:"
        echo "   點擊 'Verify connection' 按鈕"
        echo "   應該看到: ✅ 'Connected successfully - $RAG_MODELS models found'"
        echo ""
        echo "6. 保存設定:"
        echo "   點擊 'Save' 按鈕"
        echo ""
        echo "7. 刷新頁面:"
        echo "   按 F5 或 Ctrl + F5"
        echo ""
        echo "8. 檢查模型選擇器:"
        echo "   新對話 → 點擊模型下拉選單"
        echo "   應該看到 $RAG_MODELS 個模型"
        echo ""
    else
        echo -e "${GREEN}✅ 修復成功!${NC}"
        echo "現在 OpenWebUI 有 $AFTER_MODELS 個模型"
        echo ""
    fi
else
    echo -e "${BLUE}步驟 6: 無需修復${NC}"
    echo "=========================================="
    echo -e "${GREEN}✅ OpenWebUI 已正確同步模型${NC}"
    echo ""
fi

# 總結
echo ""
echo "=========================================="
echo -e "${BLUE}診斷總結${NC}"
echo "=========================================="
echo ""
echo "Ollama 模型數: $OLLAMA_MODELS (其中 $RAG_MODELS 個 RAG 模型)"
echo "OpenWebUI 模型數: $OPENWEBUI_MODELS"
echo ""

if [ "$OPENWEBUI_MODELS" -gt "0" ]; then
    echo -e "${GREEN}✅ 狀態: 正常${NC}"
    echo ""
    echo "所有使用者(管理員和一般使用者)都應該能看到這些模型"
    echo ""
    echo "一般使用者操作:"
    echo "1. 清除瀏覽器快取 (Ctrl + Shift + Delete)"
    echo "2. 重新登入"
    echo "3. 檢查模型選擇器"
else
    echo -e "${RED}❌ 狀態: 需要手動配置${NC}"
    echo ""
    echo "請按照上述步驟在 Admin Panel 中配置 Ollama 連接"
fi

echo ""
echo "=========================================="
echo "完成!"
echo "=========================================="
echo ""

# 顯示可用的 RAG 模型
if [ "$RAG_MODELS" -gt "0" ]; then
    echo "可用的 RAG 模型示例:"
    docker exec art-history-ollama ollama list | grep "rag" | head -10 | while read line; do
        MODEL_NAME=$(echo "$line" | awk '{print $1}')
        echo "  - $MODEL_NAME"
    done
    echo ""
fi
