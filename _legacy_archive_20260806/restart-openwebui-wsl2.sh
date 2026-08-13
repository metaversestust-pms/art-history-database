#!/bin/bash
# WSL2 環境下重啟 OpenWebUI 的自動化腳本
# 自動獲取 WSL2 IP 並配置 OpenWebUI

echo "=========================================="
echo "🔧 OpenWebUI WSL2 自動配置工具"
echo "=========================================="
echo ""

# 獲取 WSL2 IP 地址
echo "🔍 獲取 WSL2 IP 地址..."
WSL_IP=$(ip addr show eth0 | grep "inet " | awk '{print $2}' | cut -d/ -f1)

if [ -z "$WSL_IP" ]; then
    echo "   ❌ 錯誤: 無法獲取 WSL2 IP 地址"
    echo ""
    echo "   請檢查網絡配置:"
    echo "   ip addr show"
    exit 1
fi

echo "   ✅ WSL2 IP: $WSL_IP"
echo ""

# 檢查 Ollama RAG Proxy 是否運行
echo "🔍 檢查 Ollama RAG Proxy 狀態..."
if curl -s http://localhost:11435/health > /dev/null 2>&1; then
    echo "   ✅ Ollama RAG Proxy 運行正常"
else
    echo "   ❌ Ollama RAG Proxy 未運行"
    echo ""
    echo "   請先啟動 Ollama RAG Proxy:"
    echo "   cd /mnt/c/Users/ssking1999/Desktop/藝術史資料庫/art-history-database"
    echo "   node ollama-rag-proxy.js > ollama-rag-proxy.log 2>&1 &"
    exit 1
fi

echo ""

# 檢查 Multi-DB RAG Server 是否運行
echo "🔍 檢查 Multi-DB RAG Server 狀態..."
if curl -s http://localhost:8010/health > /dev/null 2>&1; then
    echo "   ✅ Multi-DB RAG Server 運行正常"
else
    echo "   ⚠️  Multi-DB RAG Server 未運行"
    echo ""
    echo "   請先啟動 Multi-DB RAG Server:"
    echo "   cd /mnt/c/Users/ssking1999/Desktop/藝術史資料庫/art-history-database"
    echo "   node multi-database-rag-server.js > multi-database-rag-server.log 2>&1 &"
    exit 1
fi

echo ""

# 停止現有 OpenWebUI 容器
echo "🛑 停止現有 OpenWebUI 容器..."
if docker ps -a | grep -q art-history-openwebui; then
    docker stop art-history-openwebui > /dev/null 2>&1
    docker rm art-history-openwebui > /dev/null 2>&1
    echo "   ✅ 已停止並刪除舊容器"
else
    echo "   ℹ️  沒有找到舊容器"
fi

echo ""

# 啟動新的 OpenWebUI 容器
echo "🚀 啟動 OpenWebUI（使用 WSL2 IP）..."
CONTAINER_ID=$(docker run -d \
  --name art-history-openwebui \
  --restart always \
  -p 8080:8080 \
  -e OLLAMA_BASE_URL=http://${WSL_IP}:11435 \
  -e WEBUI_AUTH=false \
  -v open-webui:/app/backend/data \
  ghcr.io/open-webui/open-webui:main 2>&1)

if [ $? -eq 0 ]; then
    echo "   ✅ 容器已啟動"
    echo "   容器 ID: ${CONTAINER_ID:0:12}"
else
    echo "   ❌ 啟動失敗"
    echo "   錯誤: $CONTAINER_ID"
    exit 1
fi

echo ""

# 等待容器啟動
echo "⏳ 等待容器啟動..."
for i in {1..15}; do
    sleep 1
    echo -n "."
done
echo ""

# 等待 OpenWebUI 服務就緒
echo ""
echo "⏳ 等待 OpenWebUI 服務就緒..."
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8080 > /dev/null 2>&1; then
        echo "   ✅ OpenWebUI 服務已就緒"
        break
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo -n "."
    sleep 1
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo ""
    echo "   ⚠️  OpenWebUI 啟動時間較長，但容器正在運行"
fi

echo ""

# 驗證連接
echo "✅ 驗證 OpenWebUI → Ollama Proxy 連接..."
sleep 2

if docker exec art-history-openwebui curl -s http://${WSL_IP}:11435/health > /dev/null 2>&1; then
    echo "   ✅ OpenWebUI 成功連接到 Ollama RAG Proxy！"
else
    echo "   ❌ 連接失敗"
    echo ""
    echo "   請檢查:"
    echo "   1. Ollama RAG Proxy 是否運行: curl http://localhost:11435/health"
    echo "   2. 防火牆是否允許端口 11435"
    exit 1
fi

echo ""

# 測試模型列表
echo "📊 測試 RAG 模型列表..."
RAG_MODELS=$(docker exec art-history-openwebui curl -s http://${WSL_IP}:11435/api/tags 2>/dev/null | grep -o '"name":"[^"]*-vector_rag"' | head -3)

if [ -n "$RAG_MODELS" ]; then
    echo "   ✅ RAG 模型可訪問"
    echo ""
    echo "   示例模型:"
    echo "$RAG_MODELS" | sed 's/"name":"//g' | sed 's/"//g' | sed 's/^/     • /'
else
    echo "   ⚠️  無法獲取模型列表（可能需要等待更長時間）"
fi

echo ""
echo "=========================================="
echo "🎉 配置完成！"
echo "=========================================="
echo ""
echo "📊 配置摘要:"
echo "   • WSL2 IP: $WSL_IP"
echo "   • OLLAMA_BASE_URL: http://${WSL_IP}:11435"
echo "   • OpenWebUI: http://localhost:8080"
echo ""
echo "🎯 下一步:"
echo "   1. 訪問: http://localhost:8080"
echo "   2. 在模型選擇中選擇 RAG 組合模型"
echo "   3. 開始提問藝術史問題！"
echo ""
echo "💡 推薦模型:"
echo "   • llama3.1-vector_rag (快速檢索)"
echo "   • qwen2.5-hybrid_rag (中文優化)"
echo "   • llama3.1-graph_rag (關係探索)"
echo ""
echo "📚 文檔:"
echo "   • WSL2環境配置說明.md"
echo "   • 配置完成_開始使用.md"
echo "   • ollama-rag-proxy使用指南.md"
echo ""
echo "=========================================="
echo ""
