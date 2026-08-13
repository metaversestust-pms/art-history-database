#!/bin/bash

# ============================================================
# 藝術史資料庫 - OpenWebUI 重啟腳本
# ============================================================

set -e

# 顏色定義
GREEN='\033[0;32m'
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
echo "║          🔄 重啟 OpenWebUI 服務                        ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

cd "$(dirname "$0")"

# 停止服務
log_info "停止現有服務..."
./stop-openwebui.sh

echo ""
log_info "等待 5 秒..."
sleep 5

# 啟動服務
log_info "啟動服務..."
./start-openwebui.sh

echo ""
log_success "OpenWebUI 服務已重啟"
echo ""
