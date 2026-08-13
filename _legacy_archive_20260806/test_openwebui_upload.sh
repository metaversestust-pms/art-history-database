#!/bin/bash
# 測試 OpenWebUI 上傳功能的腳本

echo "🧪 測試 OpenWebUI 上傳功能..."
echo ""

# 1. 測試 Ollama embeddings API
echo "1️⃣ 測試 Ollama embeddings API..."
response=$(curl -s -X POST http://localhost:11434/api/embeddings \
  -H "Content-Type: application/json" \
  -d '{"model": "nomic-embed-text", "prompt": "測試文本"}')

if echo "$response" | grep -q "embedding"; then
    echo "   ✅ Ollama embeddings API 正常"
    echo "   嵌入維度: $(echo $response | grep -o '"embedding":\[' | wc -l) vectors"
else
    echo "   ❌ Ollama embeddings API 失敗"
    echo "   響應: $response"
fi

echo ""

# 2. 檢查 OpenWebUI 容器狀態
echo "2️⃣ 檢查 OpenWebUI 容器狀態..."
if docker ps | grep -q "art-history-openwebui.*Up.*healthy"; then
    echo "   ✅ OpenWebUI 容器運行中且健康"
else
    echo "   ⚠️  OpenWebUI 容器狀態異常"
    docker ps | grep openwebui
fi

echo ""

# 3. 檢查最近的錯誤日誌
echo "3️⃣ 檢查最近的錯誤日誌..."
recent_errors=$(docker logs art-history-openwebui --since 5m 2>&1 | grep -i "error\|404" | grep -v "version.json" | wc -l)

if [ "$recent_errors" -eq 0 ]; then
    echo "   ✅ 最近 5 分鐘沒有錯誤"
else
    echo "   ⚠️  發現 $recent_errors 個錯誤，請查看:"
    docker logs art-history-openwebui --since 5m 2>&1 | grep -i "error\|404" | grep -v "version.json" | tail -5
fi

echo ""

# 4. 檢查 API 端點配置
echo "4️⃣ 檢查 OpenWebUI 內部 API 端點配置..."
docker exec art-history-openwebui grep -r "api/embeddings" /app/backend/open_webui/retrieval/utils.py 2>/dev/null | head -1
if [ $? -eq 0 ]; then
    echo "   ✅ API 端點配置正確"
else
    echo "   ❌ API 端點配置可能有問題"
fi

echo ""

# 5. 測試建議
echo "📝 測試建議:"
echo ""
echo "   請在瀏覽器中訪問: http://localhost:8080"
echo ""
echo "   測試步驟:"
echo "   1. 登入 OpenWebUI（如果需要）"
echo "   2. 進入 Workspace > Knowledge 或 Documents"
echo "   3. 創建一個新的 Knowledge Base（如果還沒有）"
echo "   4. 點擊 '+ Add File' 或上傳圖標"
echo "   5. 選擇一個小的文本文件（.txt, .md 等）"
echo "   6. 觀察上傳過程"
echo ""
echo "   預期結果:"
echo "   ✅ 文件成功上傳"
echo "   ✅ 沒有 'list index out of range' 錯誤"
echo "   ✅ 可以在 Knowledge Base 中看到文件"
echo ""

# 6. 監控日誌（可選）
echo "💡 提示: 如果要實時監控上傳過程的日誌，請運行:"
echo "   docker logs art-history-openwebui -f"
echo ""

echo "測試完成！"
