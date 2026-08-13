#!/bin/bash

# ============================================================
# 藝術史資料庫 - OpenWebUI 快速啟動腳本
# ============================================================
# 功能：
# 1. 創建必要的網路和目錄
# 2. 啟動所有服務
# 3. 下載必要的模型
# 4. 驗證服務狀態
# ============================================================

set -e  # 遇到錯誤立即退出

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日誌函數
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 顯示標題
echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║   🎨 藝術史資料庫 OpenWebUI 部署系統                  ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# 檢查 Docker 是否運行
log_info "檢查 Docker 環境..."
if ! docker info > /dev/null 2>&1; then
    log_error "Docker 未運行，請先啟動 Docker"
    exit 1
fi
log_success "Docker 環境正常"

# 檢查 Docker Compose
if ! command -v docker-compose &> /dev/null; then
    log_error "未找到 docker-compose，請先安裝"
    exit 1
fi
log_success "docker-compose 已安裝"

# 進入工作目錄
cd "$(dirname "$0")"
log_info "當前工作目錄: $(pwd)"

# ============================================================
# 步驟 1: 創建必要的目錄
# ============================================================
log_info "創建必要的目錄結構..."

mkdir -p logs/openwebui
mkdir -p openwebui-config
mkdir -p models
mkdir -p data/chroma

log_success "目錄創建完成"

# ============================================================
# 步驟 2: 創建 Docker 網路
# ============================================================
log_info "創建 Docker 網路..."

if ! docker network inspect art-history-network > /dev/null 2>&1; then
    docker network create art-history-network
    log_success "Docker 網路創建成功: art-history-network"
else
    log_warning "Docker 網路已存在: art-history-network"
fi

# ============================================================
# 步驟 3: 複製環境變數文件
# ============================================================
if [ ! -f ".env" ]; then
    log_info "創建環境變數文件..."
    if [ -f ".env.openwebui" ]; then
        cp .env.openwebui .env
        log_success "已從 .env.openwebui 創建 .env 文件"
    else
        log_warning "未找到 .env.openwebui，使用默認配置"
    fi
else
    log_warning ".env 文件已存在，跳過創建"
fi

# ============================================================
# 步驟 4: 啟動核心服務（如果未運行）
# ============================================================
log_info "檢查核心服務狀態..."

# 檢查 PostgreSQL
if ! docker ps | grep -q art-database-postgres; then
    log_warning "PostgreSQL 未運行，正在啟動核心服務..."
    docker-compose up -d postgres redis elasticsearch
    log_info "等待資料庫啟動..."
    sleep 10
else
    log_success "核心服務已在運行"
fi

# ============================================================
# 步驟 5: 啟動 Neo4j
# ============================================================
log_info "啟動 Neo4j 知識圖譜..."

if [ -f "docker-compose.neo4j.yml" ]; then
    docker-compose -f docker-compose.neo4j.yml up -d
    log_success "Neo4j 已啟動"
else
    log_warning "未找到 docker-compose.neo4j.yml"
fi

# ============================================================
# 步驟 6: 啟動 OpenWebUI 相關服務
# ============================================================
log_info "啟動 OpenWebUI 服務..."

docker-compose -f docker-compose.openwebui.yml up -d

log_success "OpenWebUI 服務已啟動"

# ============================================================
# 步驟 7: 等待服務就緒
# ============================================================
log_info "等待服務啟動完成..."

# 等待 Ollama
log_info "等待 Ollama 啟動 (30秒)..."
sleep 30

# 檢查 Ollama 是否就緒
MAX_RETRIES=10
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        log_success "Ollama 服務就緒"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    log_info "等待 Ollama... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 3
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    log_error "Ollama 啟動超時"
    exit 1
fi

# 等待 OpenWebUI
log_info "等待 OpenWebUI 啟動 (15秒)..."
sleep 15

# ============================================================
# 步驟 8: 檢查服務狀態
# ============================================================
log_info "檢查服務狀態..."

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║                    服務狀態檢查                        ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# 檢查各個服務
check_service() {
    SERVICE_NAME=$1
    URL=$2

    if curl -s -f "$URL" > /dev/null 2>&1; then
        log_success "$SERVICE_NAME: $URL"
        return 0
    else
        log_warning "$SERVICE_NAME: $URL (未響應)"
        return 1
    fi
}

check_service "Ollama API" "http://localhost:11434/api/tags"
check_service "OpenWebUI" "http://localhost:8080"
check_service "ChromaDB" "http://localhost:8001/api/v1/heartbeat"

# 檢查其他服務
if curl -s http://localhost:7474 > /dev/null 2>&1; then
    log_success "Neo4j Browser: http://localhost:7474"
fi

if curl -s http://localhost:9200 > /dev/null 2>&1; then
    log_success "Elasticsearch: http://localhost:9200"
fi

# ============================================================
# 步驟 9: 顯示 Docker 容器狀態
# ============================================================
echo ""
log_info "Docker 容器狀態："
docker ps --filter "name=art-history" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# ============================================================
# 完成提示
# ============================================================
echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║                  🎉 部署完成！                         ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
log_success "OpenWebUI 已成功啟動！"
echo ""
echo "📌 訪問地址："
echo "   • OpenWebUI:     http://localhost:8080"
echo "   • Ollama API:    http://localhost:11434"
echo "   • Neo4j Browser: http://localhost:7474"
echo "   • ChromaDB:      http://localhost:8001"
echo ""
echo "📚 下一步操作："
echo "   1. 執行 ./download-models.sh 下載 LLM 模型"
echo "   2. 執行 ./register-models.sh 註冊 RAG 模型組合"
echo "   3. 訪問 OpenWebUI 開始使用"
echo ""
echo "💡 提示："
echo "   • 查看日誌: docker-compose -f docker-compose.openwebui.yml logs -f"
echo "   • 停止服務: ./stop-openwebui.sh"
echo "   • 重啟服務: ./restart-openwebui.sh"
echo ""
