#!/bin/bash
# 創建完整的LLM+RAG組合模型
# 支援所有基礎模型 × 所有RAG策略

echo "🎨 創建完整的LLM+RAG組合模型集合"
echo "==========================================="
echo ""
echo "基礎模型: llama3.1:8b, qwen3:4b, qwen3:8b, deepseek-r1:8b, gemma3:4b"
echo "RAG策略: vector, graph, hybrid, advanced, agentic, self, naive"
echo ""
echo "目標: 創建 35+ 個組合模型"
echo "==========================================="
echo ""

# 進入Ollama容器執行
docker exec art-history-ollama bash -c '

# 定義RAG策略系統提示模板
function create_rag_model() {
    local model_name=$1
    local base_model=$2
    local rag_strategy=$3
    local rag_display=$4
    local description=$5

    echo "創建: $model_name"

    cat > /tmp/${model_name}.modelfile << EOF
FROM ${base_model}

SYSTEM """你是一位專業的藝術史學者，專精於中國傳統藝術和西方藝術史。

當前配置：
- RAG策略: ${rag_strategy} (${rag_display})
- 基礎模型: ${base_model}
- 組合ID: ${model_name}

特色：${description}

請基於檢索到的藝術史知識，提供準確、詳細且富有洞察力的回答。
"""

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1
PARAMETER num_ctx 4096
EOF

    ollama create ${model_name} -f /tmp/${model_name}.modelfile
    echo "✅ ${model_name} 創建完成"
    echo ""
}

# ==================== Llama 3.1:8b 系列 ====================
echo "【1/5】創建 Llama 3.1:8b 系列..."
echo "-------------------------------------------"

# llama31-vector-rag (已存在)
echo "✓ llama31-vector-rag 已存在"

# llama31-graph-rag (已存在)
echo "✓ llama31-graph-rag 已存在"

# llama31-hybrid-rag (已存在)
echo "✓ llama31-hybrid-rag 已存在"

# 新增: Advanced RAG
create_rag_model "llama31-advanced-rag" "llama3.1:8b" "advanced_rag" "🎯 Advanced RAG" \
    "多級檢索與重排序，提供深度分析，適合複雜的藝術史研究查詢"

# 新增: Agentic RAG
create_rag_model "llama31-agentic-rag" "llama3.1:8b" "agentic_rag" "🤖 Agentic RAG" \
    "智能代理式推理，多步驟決策，適合需要邏輯推理的複雜問題"

# 新增: Self RAG
create_rag_model "llama31-self-rag" "llama3.1:8b" "self_rag" "🔄 Self RAG" \
    "自我反思策略，迭代改進答案質量，適合需要高準確性的學術查詢"

# 新增: Naive RAG
create_rag_model "llama31-naive-rag" "llama3.1:8b" "naive_rag" "⚡ Naive RAG" \
    "最簡單的檢索策略，極速響應，適合快速基礎問答"

echo "✅ Llama 3.1:8b 系列完成 (7個模型)"
echo ""

# ==================== Qwen3:4b 系列 ====================
echo "【2/5】創建 Qwen3:4b 系列..."
echo "-------------------------------------------"

# qwen3-vector-rag (已存在)
echo "✓ qwen3-vector-rag 已存在"

# qwen3-hybrid-rag (已存在)
echo "✓ qwen3-hybrid-rag 已存在"

# 新增: Graph RAG
create_rag_model "qwen3-graph-rag" "qwen3:4b" "graph_only" "🕸️ Graph RAG" \
    "知識圖譜檢索，探索概念關係，中文優化，適合關係分析查詢"

# 新增: Advanced RAG
create_rag_model "qwen3-advanced-rag" "qwen3:4b" "advanced_rag" "🎯 Advanced RAG" \
    "多級檢索與重排序，中文優化，適合深度中文藝術史研究"

# 新增: Agentic RAG
create_rag_model "qwen3-agentic-rag" "qwen3:4b" "agentic_rag" "🤖 Agentic RAG" \
    "智能代理式推理，中文優化，適合複雜的中文邏輯推理問題"

# 新增: Self RAG
create_rag_model "qwen3-self-rag" "qwen3:4b" "self_rag" "🔄 Self RAG" \
    "自我反思策略，中文優化，適合需要高準確性的中文學術查詢"

# 新增: Naive RAG
create_rag_model "qwen3-naive-rag" "qwen3:4b" "naive_rag" "⚡ Naive RAG" \
    "極速檢索，中文優化，適合快速中文基礎問答"

echo "✅ Qwen3:4b 系列完成 (7個模型)"
echo ""

# ==================== Qwen3:8b 系列 ====================
echo "【3/5】創建 Qwen3:8b 系列..."
echo "-------------------------------------------"

# qwen3-8b-graph-rag (已存在)
echo "✓ qwen3-8b-graph-rag 已存在"

# 新增: Vector RAG
create_rag_model "qwen3-8b-vector-rag" "qwen3:8b" "vector_only" "🔍 Vector RAG" \
    "純向量檢索，8B參數，中文優化，適合語義相似性查詢"

# 新增: Hybrid RAG
create_rag_model "qwen3-8b-hybrid-rag" "qwen3:8b" "hybrid_balanced" "⚖️ Hybrid RAG" \
    "平衡混合策略，8B參數，中文優化，適合通用中文問答"

# 新增: Advanced RAG
create_rag_model "qwen3-8b-advanced-rag" "qwen3:8b" "advanced_rag" "🎯 Advanced RAG" \
    "多級檢索，8B參數，中文優化，適合深度複雜分析"

# 新增: Agentic RAG
create_rag_model "qwen3-8b-agentic-rag" "qwen3:8b" "agentic_rag" "🤖 Agentic RAG" \
    "智能代理推理，8B參數，中文優化，適合複雜邏輯推理"

# 新增: Self RAG
create_rag_model "qwen3-8b-self-rag" "qwen3:8b" "self_rag" "🔄 Self RAG" \
    "自我反思策略，8B參數，中文優化，適合高準確性查詢"

# 新增: Naive RAG
create_rag_model "qwen3-8b-naive-rag" "qwen3:8b" "naive_rag" "⚡ Naive RAG" \
    "極速檢索，8B參數，中文優化，適合快速問答"

echo "✅ Qwen3:8b 系列完成 (7個模型)"
echo ""

# ==================== DeepSeek-R1:8b 系列 ====================
echo "【4/5】創建 DeepSeek-R1:8b 系列..."
echo "-------------------------------------------"

# 新增: Vector RAG
create_rag_model "deepseek-vector-rag" "deepseek-r1:8b" "vector_only" "🔍 Vector RAG" \
    "純向量檢索，專注推理，適合需要邏輯分析的語義查詢"

# 新增: Graph RAG
create_rag_model "deepseek-graph-rag" "deepseek-r1:8b" "graph_only" "🕸️ Graph RAG" \
    "知識圖譜檢索，專注推理，適合關係探索和結構化查詢"

# 新增: Hybrid RAG
create_rag_model "deepseek-hybrid-rag" "deepseek-r1:8b" "hybrid_balanced" "⚖️ Hybrid RAG" \
    "平衡混合策略，專注推理，適合通用問答"

# 新增: Advanced RAG
create_rag_model "deepseek-advanced-rag" "deepseek-r1:8b" "advanced_rag" "🎯 Advanced RAG" \
    "多級檢索與重排序，專注推理，適合複雜分析"

# 新增: Agentic RAG
create_rag_model "deepseek-agentic-rag" "deepseek-r1:8b" "agentic_rag" "🤖 Agentic RAG" \
    "智能代理式推理，邏輯推理專家，適合多步驟複雜問題"

# 新增: Self RAG
create_rag_model "deepseek-self-rag" "deepseek-r1:8b" "self_rag" "🔄 Self RAG" \
    "自我反思策略，專注推理，適合需要自我驗證的查詢"

# 新增: Naive RAG
create_rag_model "deepseek-naive-rag" "deepseek-r1:8b" "naive_rag" "⚡ Naive RAG" \
    "極速檢索，專注推理，適合快速推理問答"

echo "✅ DeepSeek-R1:8b 系列完成 (7個模型)"
echo ""

# ==================== Gemma3:4b 系列 ====================
echo "【5/5】創建 Gemma3:4b 系列..."
echo "-------------------------------------------"

# 新增: Vector RAG
create_rag_model "gemma3-vector-rag" "gemma3:4b" "vector_only" "🔍 Vector RAG" \
    "純向量檢索，輕量快速，適合需要快速響應的語義查詢"

# 新增: Graph RAG
create_rag_model "gemma3-graph-rag" "gemma3:4b" "graph_only" "🕸️ Graph RAG" \
    "知識圖譜檢索，輕量快速，適合快速關係探索"

# 新增: Hybrid RAG
create_rag_model "gemma3-hybrid-rag" "gemma3:4b" "hybrid_balanced" "⚖️ Hybrid RAG" \
    "平衡混合策略，輕量快速，適合日常通用問答"

# 新增: Advanced RAG
create_rag_model "gemma3-advanced-rag" "gemma3:4b" "advanced_rag" "🎯 Advanced RAG" \
    "多級檢索，輕量模型，適合資源受限的複雜查詢"

# 新增: Agentic RAG
create_rag_model "gemma3-agentic-rag" "gemma3:4b" "agentic_rag" "🤖 Agentic RAG" \
    "智能代理推理，輕量快速，適合快速多步驟決策"

# 新增: Self RAG
create_rag_model "gemma3-self-rag" "gemma3:4b" "self_rag" "🔄 Self RAG" \
    "自我反思策略，輕量模型，適合快速質量驗證"

# 新增: Naive RAG
create_rag_model "gemma3-naive-rag" "gemma3:4b" "naive_rag" "⚡ Naive RAG" \
    "極速檢索，最輕量組合，適合極速基礎問答"

echo "✅ Gemma3:4b 系列完成 (7個模型)"
echo ""

echo "==========================================="
echo "🎉 所有RAG組合模型創建完成！"
echo ""
echo "統計："
echo "- Llama 3.1:8b: 7個RAG組合"
echo "- Qwen3:4b: 7個RAG組合"
echo "- Qwen3:8b: 7個RAG組合"
echo "- DeepSeek-R1:8b: 7個RAG組合"
echo "- Gemma3:4b: 7個RAG組合"
echo ""
echo "總計: 35個LLM+RAG組合模型"
echo "==========================================="
echo ""
echo "驗證模型列表："
ollama list | grep -E "(rag|RAG)"

'

echo ""
echo "🎉 完成！現在請刷新OpenWebUI頁面查看新模型！"
echo ""
echo "建議使用："
echo "  🚀 llama31-hybrid-rag - 最平衡的選擇"
echo "  🎯 deepseek-advanced-rag - 複雜分析"
echo "  ⚡ gemma3-naive-rag - 極速響應"
echo "  🕸️ qwen3-8b-graph-rag - 關係探索"
