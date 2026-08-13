#!/bin/bash

# ============================================================
# 藝術史資料庫 - RAG 模型組合註冊腳本
# ============================================================
# 功能：
# 1. 啟動 RAG 管理器
# 2. 啟動 OpenWebUI 整合服務
# 3. 註冊 RAG+LLM 模型組合
# ============================================================

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

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

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║        🎨 RAG 模型組合註冊工具                        ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# 進入工作目錄
cd "$(dirname "$0")"

# ============================================================
# 步驟 1: 檢查必要服務
# ============================================================
log_info "檢查必要服務狀態..."

# 檢查 Ollama
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    log_error "Ollama 服務未運行，請先執行 ./start-openwebui.sh"
    exit 1
fi
log_success "Ollama 服務正常"

# 檢查 OpenWebUI
if ! curl -s http://localhost:8080 > /dev/null 2>&1; then
    log_error "OpenWebUI 服務未運行，請先執行 ./start-openwebui.sh"
    exit 1
fi
log_success "OpenWebUI 服務正常"

# 檢查 Neo4j
if ! curl -s http://localhost:7474 > /dev/null 2>&1; then
    log_warning "Neo4j 服務未運行，Graph RAG 功能將無法使用"
    read -p "是否繼續？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
else
    log_success "Neo4j 服務正常"
fi

# ============================================================
# 步驟 2: 啟動 RAG 管理器
# ============================================================
log_info "啟動 RAG 管理器..."

# 檢查 RAG 管理器是否已運行
if curl -s http://localhost:8007/health > /dev/null 2>&1; then
    log_warning "RAG 管理器已在運行"
else
    log_info "正在啟動 RAG 管理器..."

    # 確保目錄存在
    mkdir -p logs

    # 啟動 RAG 管理器（背景執行）
    cd langchain-rag
    nohup python3 unified_rag_manager.py > ../logs/rag_manager.log 2>&1 &
    RAG_MANAGER_PID=$!
    echo $RAG_MANAGER_PID > ../logs/rag_manager.pid
    cd ..

    log_info "等待 RAG 管理器啟動..."
    sleep 10

    # 驗證啟動
    if curl -s http://localhost:8007/health > /dev/null 2>&1; then
        log_success "RAG 管理器已啟動 (PID: $RAG_MANAGER_PID)"
    else
        log_error "RAG 管理器啟動失敗，請檢查日誌: logs/rag_manager.log"
        exit 1
    fi
fi

# ============================================================
# 步驟 3: 啟動 OpenWebUI 整合服務
# ============================================================
log_info "啟動 OpenWebUI 整合服務..."

# 檢查整合服務是否已運行
if curl -s http://localhost:8009/health > /dev/null 2>&1; then
    log_warning "OpenWebUI 整合服務已在運行"
else
    log_info "正在啟動 OpenWebUI 整合服務..."

    # 啟動整合服務（背景執行）
    nohup python3 openwebui_integration.py > logs/openwebui_integration.log 2>&1 &
    INTEGRATION_PID=$!
    echo $INTEGRATION_PID > logs/openwebui_integration.pid

    log_info "等待整合服務啟動..."
    sleep 10

    # 驗證啟動
    if curl -s http://localhost:8009/health > /dev/null 2>&1; then
        log_success "OpenWebUI 整合服務已啟動 (PID: $INTEGRATION_PID)"
    else
        log_error "整合服務啟動失敗，請檢查日誌: logs/openwebui_integration.log"
        exit 1
    fi
fi

# ============================================================
# 步驟 4: 註冊模型組合
# ============================================================
log_info "註冊 RAG+LLM 模型組合..."

# 檢查是否有註冊腳本
if [ -f "openwebui_model_registration.py" ]; then
    log_info "執行模型註冊..."
    python3 openwebui_model_registration.py

    if [ $? -eq 0 ]; then
        log_success "模型組合註冊成功"
    else
        log_warning "模型註冊可能失敗，請檢查錯誤信息"
    fi
else
    log_warning "未找到 openwebui_model_registration.py，將使用手動註冊"

    # 手動註冊示例
    echo ""
    log_info "請按照以下步驟手動註冊模型："
    echo ""
    echo "1. 訪問 OpenWebUI: http://localhost:8080"
    echo "2. 進入 Settings > Functions"
    echo "3. 上傳 enhanced_openwebui_rag_function_v3.py"
    echo "4. 啟用該函數"
    echo ""
fi

# ============================================================
# 步驟 5: 檢查已下載的模型
# ============================================================
log_info "檢查已下載的模型..."
echo ""

docker exec art-history-ollama ollama list

# ============================================================
# 步驟 6: 顯示可用的 RAG 策略
# ============================================================
echo ""
log_info "可用的 RAG 策略："
echo ""
echo "  🔍 vector_only      - 純向量語義檢索"
echo "  🕸️  graph_only       - Neo4j 知識圖譜檢索"
echo "  ⚖️  hybrid_balanced  - 混合策略（向量 + 圖譜）"
echo "  🎯 advanced_rag     - 多級檢索與重排序"
echo "  🤖 agentic_rag      - 智能代理式推理"
echo "  🔄 self_rag         - 自我反思迭代改進"
echo ""

# ============================================================
# 步驟 7: 測試 API
# ============================================================
log_info "測試 RAG API..."
echo ""

# 測試 RAG 管理器
log_info "測試 RAG 管理器 API..."
curl -s http://localhost:8007/health | python3 -m json.tool 2>/dev/null || log_warning "RAG 管理器 API 無響應"

echo ""

# 測試整合服務
log_info "測試 OpenWebUI 整合 API..."
curl -s http://localhost:8009/health | python3 -m json.tool 2>/dev/null || log_warning "整合服務 API 無響應"

# ============================================================
# 完成提示
# ============================================================
echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║            🎉 註冊完成！                               ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
log_success "RAG 模型組合已成功配置"
echo ""
echo "📌 服務狀態："
echo "   • OpenWebUI:        http://localhost:8080"
echo "   • RAG 管理器 API:    http://localhost:8007"
echo "   • 整合服務 API:      http://localhost:8009"
echo "   • Ollama API:       http://localhost:11434"
echo "   • Neo4j Browser:    http://localhost:7474"
echo ""
echo "📚 使用方式："
echo ""
echo "   1. 訪問 OpenWebUI: http://localhost:8080"
echo "   2. 在左上角模型選擇器中查看可用模型："
echo "      - 🔍 Llama 3.1 8B + 向量RAG"
echo "      - 🕸️ Llama 3.1 8B + 圖譜RAG"
echo "      - ⚖️ Llama 3.1 8B + 混合RAG"
echo "      - ... 等 30 種組合"
echo ""
echo "   3. 選擇模型後，開始提問："
echo "      例如：「達文西有哪些著名的藝術作品？」"
echo ""
echo "💡 提示："
echo "   • 查看 RAG 管理器日誌: tail -f logs/rag_manager.log"
echo "   • 查看整合服務日誌: tail -f logs/openwebui_integration.log"
echo "   • 停止服務: ./stop-services.sh"
echo ""
echo "🔍 測試查詢範例："
echo "   • 文藝復興時期有哪些代表性藝術家？"
echo "   • 比較印象派和後印象派的差異"
echo "   • 巴洛克藝術的特點是什麼？"
echo ""
