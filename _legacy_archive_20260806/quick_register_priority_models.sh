#!/bin/bash
# 快速註冊優先級RAG+LLM組合模型到Ollama

echo "🎨 藝術史RAG+LLM組合模型快速註冊腳本"
echo "============================================"
echo ""

# 檢查Ollama是否安裝
if ! command -v ollama &> /dev/null; then
    echo "❌ 錯誤: 未找到Ollama，請先安裝 Ollama"
    echo "   安裝指令: curl -fsSL https://ollama.com/install.sh | sh"
    exit 1
fi

# 檢查RAG服務是否運行
echo "🔍 檢查RAG服務狀態..."
if curl -s http://localhost:8008/health > /dev/null 2>&1; then
    echo "✅ RAG服務運行正常 (端口8008)"
else
    echo "❌ 警告: RAG服務未運行，請先啟動RAG管理API"
    echo "   啟動指令: cd langchain-rag && python3 unified_rag_manager.py"
    echo ""
    read -p "是否繼續註冊模型？(y/N): " continue_anyway
    if [[ ! $continue_anyway =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "📋 準備註冊以下優先級模型:"
echo "1. qwen3-4b-basic_rag (中文場景最佳)"
echo "2. gpt-oss-20b-agentic_rag (最強智能分析)"
echo "3. gemma3-1b-naive_rag (極速響應)"
echo ""

read -p "是否開始註冊？(Y/n): " confirm
if [[ $confirm =~ ^[Nn]$ ]]; then
    echo "註冊已取消"
    exit 0
fi

echo ""
echo "🚀 開始註冊模型..."

# 註冊函數
register_model() {
    local model_name=$1
    local modelfile_path=$2

    echo ""
    echo "📝 註冊模型: $model_name"
    echo "   Modelfile: $modelfile_path"

    if [ ! -f "$modelfile_path" ]; then
        echo "❌ 錯誤: Modelfile 不存在: $modelfile_path"
        return 1
    fi

    # 執行ollama create命令
    if ollama create "$model_name" -f "$modelfile_path"; then
        echo "✅ 成功註冊: $model_name"
        return 0
    else
        echo "❌ 註冊失敗: $model_name"
        return 1
    fi
}

# 註冊計數器
success_count=0
total_count=3

# 註冊優先級模型
register_model "qwen3-4b-basic_rag" "modelfiles/qwen3-4b-basic_rag.Modelfile"
if [ $? -eq 0 ]; then ((success_count++)); fi

register_model "gpt-oss-20b-agentic_rag" "modelfiles/gpt-oss-20b-agentic_rag.Modelfile"
if [ $? -eq 0 ]; then ((success_count++)); fi

register_model "gemma3-1b-naive_rag" "modelfiles/gemma3-1b-naive_rag.Modelfile"
if [ $? -eq 0 ]; then ((success_count++)); fi

echo ""
echo "📊 註冊完成統計:"
echo "   成功: $success_count/$total_count"
echo ""

if [ $success_count -eq $total_count ]; then
    echo "🎉 所有優先級模型註冊成功！"
    echo ""
    echo "📱 下一步操作:"
    echo "1. 在OpenWebUI中確認模型可見"
    echo "2. 上傳 enhanced_openwebui_rag_function_v3.py 函數"
    echo "3. 測試每個模型的功能"
    echo ""
    echo "🧪 測試建議:"
    echo "   qwen3-4b-basic_rag: 印象派的特色是什麼？"
    echo "   gpt-oss-20b-agentic_rag: 分析達文西的藝術技法演進"
    echo "   gemma3-1b-naive_rag: 梵谷"
else
    echo "⚠️  部分模型註冊失敗，請檢查錯誤信息"
    echo ""
    echo "🔍 故障排除建議:"
    echo "1. 確認基礎模型已下載: ollama list"
    echo "2. 檢查Modelfile語法: ollama create --help"
    echo "3. 查看詳細錯誤: ollama logs"
fi

echo ""
echo "📋 查看已註冊模型: ollama list"
echo "🗑️  刪除模型: ollama rm <model-name>"
echo ""
echo "👋 註冊腳本執行完成！"