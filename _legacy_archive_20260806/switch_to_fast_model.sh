#!/bin/bash
# OpenWebUI 速度優化 - 一鍵切換快速模型

echo "========================================"
echo "🚀 OpenWebUI 速度優化工具"
echo "========================================"
echo ""
echo "當前使用模型: qwen3:30b (19GB, 回答速度 8-15秒)"
echo ""
echo "可用的快速模型："
echo ""
echo "1) qwen2.5:7b    [推薦]"
echo "   - 模型大小: 4.7 GB"
echo "   - 回答速度: 1-2 秒 ⭐⭐⭐"
echo "   - 品質: 優秀"
echo "   - 適合: 大多數場景"
echo ""
echo "2) qwen2.5:14b   [平衡]"
echo "   - 模型大小: 8 GB"
echo "   - 回答速度: 3-5 秒 ⭐⭐"
echo "   - 品質: 非常好"
echo "   - 適合: 需要詳細回答"
echo ""
echo "3) llama3.2:3b   [極速]"
echo "   - 模型大小: 2 GB"
echo "   - 回答速度: <1 秒 ⭐⭐⭐"
echo "   - 品質: 良好"
echo "   - 適合: 快速互動"
echo ""
echo "4) gemma2:9b     [多語言]"
echo "   - 模型大小: 5.4 GB"
echo "   - 回答速度: 2-3 秒 ⭐⭐"
echo "   - 品質: 優秀"
echo "   - 適合: 多語言問答"
echo ""
echo "5) 不切換，返回"
echo ""

read -p "請選擇要使用的模型 (1-5): " choice

case $choice in
    1)
        MODEL="qwen2.5:7b"
        SIZE="4.7GB"
        SPEED="1-2秒"
        ;;
    2)
        MODEL="qwen2.5:14b"
        SIZE="8GB"
        SPEED="3-5秒"
        ;;
    3)
        MODEL="llama3.2:3b"
        SIZE="2GB"
        SPEED="<1秒"
        ;;
    4)
        MODEL="gemma2:9b"
        SIZE="5.4GB"
        SPEED="2-3秒"
        ;;
    5)
        echo "已取消"
        exit 0
        ;;
    *)
        echo "❌ 無效選擇"
        exit 1
        ;;
esac

echo ""
echo "========================================"
echo "開始下載模型: $MODEL"
echo "模型大小: $SIZE"
echo "預期速度: $SPEED"
echo "========================================"
echo ""

# 檢查 Ollama 服務
if ! docker ps | grep -q art-history-ollama; then
    echo "❌ Ollama 服務未運行"
    echo "請先啟動: docker start art-history-ollama"
    exit 1
fi

echo "正在下載模型 $MODEL ..."
echo ""

docker exec art-history-ollama ollama pull $MODEL

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ 模型下載失敗"
    exit 1
fi

echo ""
echo "========================================"
echo "✅ 模型下載完成！"
echo "========================================"
echo ""
echo "現在測試模型速度..."
echo ""
echo "測試問題：「介紹文藝復興時期的三位最著名藝術家」"
echo "---"
echo ""

# 測試模型
START_TIME=$(date +%s.%N)
docker exec art-history-ollama ollama run $MODEL "介紹文藝復興時期的三位最著名藝術家，請用中文簡短回答，每位藝術家一句話介紹即可。" 2>/dev/null
END_TIME=$(date +%s.%N)

DURATION=$(echo "$END_TIME - $START_TIME" | bc)

echo ""
echo "---"
echo "⏱️  回答時間: ${DURATION} 秒"
echo ""

# 檢查當前加載的模型
echo "========================================"
echo "當前 Ollama 已加載的模型："
echo "========================================"
docker exec art-history-ollama ollama ps

echo ""
echo "========================================"
echo "🎉 優化完成！"
echo "========================================"
echo ""
echo "📋 下一步操作："
echo ""
echo "1. 訪問 OpenWebUI: http://localhost:8080"
echo ""
echo "2. 點擊右上角 ⚙️ Settings (設定)"
echo ""
echo "3. 選擇 Models 標籤"
echo ""
echo "4. 在模型列表中選擇: $MODEL"
echo ""
echo "5. 測試提問速度（應該比之前快 ${SPEED}）"
echo ""
echo "💡 建議啟用串流回答以獲得更好體驗："
echo "   Settings → Interface → Enable streaming: ON"
echo ""
echo "========================================"
echo ""

# 顯示比較
echo "📊 速度對比："
echo ""
echo "  優化前 (qwen3:30b):     8-15 秒"
echo "  優化後 ($MODEL):     $SPEED"
echo ""
if [ "$choice" == "1" ]; then
    echo "  預期提升: 5-10 倍 ⭐⭐⭐"
elif [ "$choice" == "2" ]; then
    echo "  預期提升: 2-3 倍 ⭐⭐"
elif [ "$choice" == "3" ]; then
    echo "  預期提升: 10-15 倍 ⭐⭐⭐"
elif [ "$choice" == "4" ]; then
    echo "  預期提升: 3-5 倍 ⭐⭐"
fi
echo ""
echo "========================================"
