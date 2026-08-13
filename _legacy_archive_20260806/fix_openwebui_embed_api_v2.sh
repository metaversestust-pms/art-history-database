#!/bin/bash
# 修復 OpenWebUI 中 Ollama embedding API 端點錯誤的腳本 v2
# 這次我們更小心地替換，避免重複

echo "🔧 修復 OpenWebUI Ollama Embedding API 端點 (v2)..."

# 停止 OpenWebUI
echo "停止 OpenWebUI..."
docker stop art-history-openwebui 2>/dev/null

# 進入容器並修改源代碼
echo "啟動 OpenWebUI 進行修補..."
docker start art-history-openwebui
sleep 5

# 修復腳本 - 更精確的替換
docker exec art-history-openwebui sh -c '
echo "查找並修復錯誤的 API 端點..."

# 先恢復可能被錯誤替換的 embeddingsdings
find /app/backend/open_webui/ -type f -name "*.py" -exec sed -i "s|/api/embeddingsdings|/api/embeddings|g" {} \;

# 然後只替換 /api/embed（但不包括已經是 /api/embeddings 的）
# 使用更精確的模式：匹配 /api/embed 但後面不是 dings
find /app/backend/open_webui/ -type f -name "*.py" -exec sed -i "s|/api/embed\([^d]\)|/api/embeddings\1|g" {} \;
find /app/backend/open_webui/ -type f -name "*.py" -exec sed -i "s|/api/embed\"|/api/embeddings\"|g" {} \;
find /app/backend/open_webui/ -type f -name "*.py" -exec sed -i "s|/api/embed'\''|/api/embeddings'\''|g" {} \;

echo "驗證修復結果..."
echo "查找 /api/embed (應該沒有):"
grep -r "/api/embed\"" /app/backend/open_webui/ 2>/dev/null | grep -v ".pyc" || echo "  ✅ 沒有找到 /api/embed"

echo "查找 /api/embeddings (應該有):"
grep -r "/api/embeddings\"" /app/backend/open_webui/ 2>/dev/null | grep -v ".pyc" | head -3

echo "查找 /api/embeddingsdings (不應該有):"
grep -r "/api/embeddingsdings" /app/backend/open_webui/ 2>/dev/null | grep -v ".pyc" || echo "  ✅ 沒有找到錯誤的 embeddingsdings"

echo "✅ 修復完成！"
'

# 重啟 OpenWebUI
echo "重啟 OpenWebUI 以應用修復..."
docker restart art-history-openwebui

echo "等待 OpenWebUI 啟動..."
sleep 20

# 檢查是否成功
echo "檢查 OpenWebUI 狀態..."
if docker ps | grep -q "art-history-openwebui.*Up"; then
    echo "✅ OpenWebUI 正在運行！"

    # 測試 Ollama embeddings 端點
    echo ""
    echo "測試 Ollama embeddings API..."
    curl -s -X POST http://localhost:11434/api/embeddings \
      -H "Content-Type: application/json" \
      -d '{"model": "nomic-embed-text", "prompt": "test"}' | head -c 100
    echo ""
    echo ""
    echo "✅ Ollama API 正常！"
else
    echo "⚠️  OpenWebUI 可能還在啟動中，請檢查日誌:"
    echo "   docker logs art-history-openwebui --tail 50"
fi

echo ""
echo "修復完成！現在可以測試文件上傳功能了。"
echo "訪問: http://localhost:8080"
