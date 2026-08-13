#!/bin/bash
# 刪除特定RAG策略的模型腳本
# 刪除: vector-rag, hybrid-rag, self-rag

echo "🗑️  準備刪除特定RAG策略模型"
echo "============================================================"
echo "將刪除的RAG策略: vector, hybrid, self"
echo "============================================================"
echo ""

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 計數器
DELETED_COUNT=0
FAILED_COUNT=0

# 獲取所有包含 vector-rag, hybrid-rag, self-rag 的模型
echo "📋 掃描現有模型..."
MODELS_TO_DELETE=$(docker exec art-history-ollama ollama list | grep -E "(vector|hybrid|self)-rag" | awk '{print $1}')

if [ -z "$MODELS_TO_DELETE" ]; then
    echo -e "${YELLOW}⚠️  沒有找到需要刪除的模型${NC}"
    exit 0
fi

# 顯示將要刪除的模型
echo ""
echo "將要刪除以下模型:"
echo "============================================================"
echo "$MODELS_TO_DELETE"
echo "============================================================"
echo ""

# 確認刪除
read -p "確認刪除這些模型? (y/n): " CONFIRM
if [ "$CONFIRM" != "y" ]; then
    echo -e "${RED}❌ 已取消刪除${NC}"
    exit 0
fi

echo ""
echo "🗑️  開始刪除模型..."
echo "============================================================"

# 刪除每個模型
while IFS= read -r MODEL_NAME; do
    if [ ! -z "$MODEL_NAME" ]; then
        echo -n "刪除: $MODEL_NAME ... "

        # 執行刪除
        if docker exec art-history-ollama ollama rm "$MODEL_NAME" 2>/dev/null; then
            echo -e "${GREEN}✅ 成功${NC}"
            ((DELETED_COUNT++))
        else
            echo -e "${RED}❌ 失敗${NC}"
            ((FAILED_COUNT++))
        fi
    fi
done <<< "$MODELS_TO_DELETE"

echo ""
echo "============================================================"
echo "📊 刪除總結"
echo "============================================================"
echo -e "${GREEN}✅ 成功刪除: $DELETED_COUNT 個模型${NC}"
if [ $FAILED_COUNT -gt 0 ]; then
    echo -e "${RED}❌ 刪除失敗: $FAILED_COUNT 個模型${NC}"
fi
echo "============================================================"

echo ""
echo "📊 剩餘模型統計"
echo "============================================================"

# 統計剩餘的RAG模型
REMAINING_ENHANCED=$(docker exec art-history-ollama ollama list | grep -c "enhanced-rag" || echo "0")
REMAINING_GRAPH=$(docker exec art-history-ollama ollama list | grep -c "graph-rag" || echo "0")
REMAINING_ADVANCED=$(docker exec art-history-ollama ollama list | grep -c "advanced-rag" || echo "0")
REMAINING_AGENTIC=$(docker exec art-history-ollama ollama list | grep -c "agentic-rag" || echo "0")
REMAINING_NAIVE=$(docker exec art-history-ollama ollama list | grep -c "naive-rag" || echo "0")

echo "Enhanced RAG: $REMAINING_ENHANCED 個"
echo "Graph RAG: $REMAINING_GRAPH 個"
echo "Advanced RAG: $REMAINING_ADVANCED 個"
echo "Agentic RAG: $REMAINING_AGENTIC 個"
echo "Naive RAG: $REMAINING_NAIVE 個"

TOTAL_REMAINING=$((REMAINING_ENHANCED + REMAINING_GRAPH + REMAINING_ADVANCED + REMAINING_AGENTIC + REMAINING_NAIVE))
echo ""
echo -e "${GREEN}總計剩餘: $TOTAL_REMAINING 個 LLM+RAG 組合${NC}"
echo "============================================================"

echo ""
echo "✅ 刪除完成！"
echo ""
echo "💡 提示:"
echo "- OpenWebUI 將自動更新模型列表"
echo "- 刪除的RAG策略: vector, hybrid, self"
echo "- 保留的RAG策略: enhanced, graph, advanced, agentic, naive"
