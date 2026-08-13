#!/bin/bash
# 修復 OpenWebUI 數據庫中的錯誤配置

echo "🔧 修復 OpenWebUI 數據庫配置..."

# 停止容器
echo "停止 OpenWebUI..."
docker stop art-history-openwebui 2>/dev/null

# 使用臨時容器掛載卷來修復數據庫
echo "創建臨時容器修復數據庫..."
docker run --rm -v openwebui_data:/data python:3.11-slim bash -c '
apt-get update -qq && apt-get install -y -qq sqlite3 > /dev/null 2>&1

cd /data

echo "檢查數據庫..."
if [ -f "webui.db" ]; then
    echo "找到 webui.db"

    # 查看當前配置
    echo "當前配置:"
    sqlite3 webui.db "SELECT key, value FROM config WHERE key LIKE \"%embed%\" OR key LIKE \"%EMBED%\";"

    # 刪除或更新錯誤的配置
    echo "修復配置..."
    sqlite3 webui.db "DELETE FROM config WHERE key = \"RAG_EMBEDDING_ENGINE\" AND value = \"sentence-transformers\";"
    sqlite3 webui.db "INSERT OR REPLACE INTO config (key, value) VALUES (\"RAG_EMBEDDING_ENGINE\", \"ollama\");"
    sqlite3 webui.db "INSERT OR REPLACE INTO config (key, value) VALUES (\"RAG_EMBEDDING_MODEL\", \"nomic-embed-text:latest\");"

    echo "修復後的配置:"
    sqlite3 webui.db "SELECT key, value FROM config WHERE key LIKE \"%embed%\" OR key LIKE \"%EMBED%\";"

    echo "✅ 數據庫配置已修復"
else
    echo "❌ 未找到 webui.db"
fi
'

echo "重新啟動 OpenWebUI..."
docker start art-history-openwebui

echo "等待啟動..."
sleep 20

echo "檢查狀態..."
if docker ps | grep -q "art-history-openwebui.*Up"; then
    echo "✅ OpenWebUI 正在運行！"
else
    echo "⚠️  OpenWebUI 還在啟動或有問題"
    echo "查看日誌:"
    docker logs art-history-openwebui --tail 30
fi
