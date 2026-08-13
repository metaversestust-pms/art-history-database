#!/bin/bash

# ============================================================
# 藝術史資料庫 - OpenWebUI 停止腳本
# ============================================================

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║          🛑 停止 OpenWebUI 服務                        ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

cd "$(dirname "$0")"

# 停止 OpenWebUI 相關服務
log_info "停止 OpenWebUI 服務..."
docker-compose -f docker-compose.openwebui.yml down

log_success "OpenWebUI 服務已停止"

# 停止背景服務
log_info "停止背景服務..."

# 停止 RAG 管理器
if [ -f "logs/rag_manager.pid" ]; then
    RAG_PID=$(cat logs/rag_manager.pid)
    if ps -p $RAG_PID > /dev/null 2>&1; then
        kill $RAG_PID
        log_success "RAG 管理器已停止 (PID: $RAG_PID)"
    fi
    rm -f logs/rag_manager.pid
fi

# 停止整合服務
if [ -f "logs/openwebui_integration.pid" ]; then
    INTEGRATION_PID=$(cat logs/openwebui_integration.pid)
    if ps -p $INTEGRATION_PID > /dev/null 2>&1; then
        kill $INTEGRATION_PID
        log_success "OpenWebUI 整合服務已停止 (PID: $INTEGRATION_PID)"
    fi
    rm -f logs/openwebui_integration.pid
fi

echo ""
log_success "所有 OpenWebUI 相關服務已停止"
echo ""
echo "💡 提示："
echo "   • 重新啟動: ./start-openwebui.sh"
echo "   • 查看狀態: docker ps"
echo ""
