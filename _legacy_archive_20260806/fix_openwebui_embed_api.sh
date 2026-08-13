#!/bin/bash
# 修復 OpenWebUI 中 Ollama embedding API 端點錯誤的腳本

echo "🔧 修復 OpenWebUI Ollama Embedding API 端點..."

# 停止 OpenWebUI
echo "停止 OpenWebUI..."
docker stop art-history-openwebui 2>/dev/null

# 進入容器並修改源代碼（需要先啟動容器）
echo "啟動 OpenWebUI 進行修補..."
docker start art-history-openwebui
sleep 5

# 修復腳本
docker exec art-history-openwebui sh -c '
# 查找使用錯誤端點的文件
echo "查找需要修復的文件..."
grep -r "/api/embed" /app/backend/open_webui/ 2>/dev/null | grep -v ".pyc" | cut -d: -f1 | sort -u

# 修復 retrieval/utils.py 文件
echo "修復 retrieval/utils.py..."
if [ -f "/app/backend/open_webui/retrieval/utils.py" ]; then
    sed -i "s|/api/embed|/api/embeddings|g" /app/backend/open_webui/retrieval/utils.py
    echo "✅ 已修復 retrieval/utils.py"
fi

# 修復其他可能的文件
for file in $(grep -rl "/api/embed" /app/backend/open_webui/ 2>/dev/null | grep -v ".pyc"); do
    echo "修復 $file..."
    sed -i "s|/api/embed|/api/embeddings|g" "$file"
    echo "✅ 已修復 $file"
done

echo "所有修復完成！"
'

# 重啟 OpenWebUI
echo "重啟 OpenWebUI 以應用修復..."
docker restart art-history-openwebui

echo "等待 OpenWebUI 啟動..."
sleep 15

# 檢查是否成功
echo "檢查 OpenWebUI 狀態..."
if docker logs art-history-openwebui --tail 20 2>&1 | grep -q "Application startup complete"; then
    echo "✅ OpenWebUI 啟動成功！"
else
    echo "⚠️  OpenWebUI 可能還在啟動中，請檢查日誌:"
    echo "   docker logs art-history-openwebui --tail 50"
fi

echo ""
echo "修復完成！現在您可以在 OpenWebUI 中測試文件上傳功能了。"
echo "訪問: http://localhost:8080"
