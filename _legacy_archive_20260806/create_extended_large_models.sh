#!/bin/bash
# 創建擴展的大型LLM+RAG組合模型
# 新增: GPT-OSS 20B, DeepSeek-R1 32B, Qwen3 30B, Llama 3.1 70B

echo "🎨 創建大型LLM+RAG組合模型集合"
echo "==========================================="
echo ""
echo "新增基礎模型:"
echo "  - gpt-oss:20b (20B參數)"
echo "  - deepseek-r1:32b (32B參數)"
echo "  - qwen3:30b (30B參數)"
echo "  - llama3.1:70b (70B參數)"
echo ""
echo "RAG策略: enhanced, hybrid, vector, graph, advanced, agentic, self, naive"
echo ""
echo "目標: 創建 32 個新組合模型 (4個LLM × 8個RAG)"
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
當回答複雜問題時，請充分利用模型的大容量參數進行深度分析。
"""

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1
PARAMETER num_ctx 8192
EOF

    ollama create ${model_name} -f /tmp/${model_name}.modelfile
    echo "✅ ${model_name} 創建完成"
    echo ""
}

# ==================== GPT-OSS 20B 系列 ====================
echo "【1/4】創建 GPT-OSS 20B 系列..."
echo "-------------------------------------------"

create_rag_model "gpt-oss-20b-enhanced-rag" "gpt-oss:20b" "enhanced_rag" "🌟 Enhanced RAG" \
    "雙資料庫檢索(Neo4j+ChromaDB)，20B參數高性能，適合複雜的藝術史研究"

create_rag_model "gpt-oss-20b-hybrid-rag" "gpt-oss:20b" "hybrid_balanced" "⚖️ Hybrid RAG" \
    "平衡混合策略，20B參數，適合通用藝術史問答"

create_rag_model "gpt-oss-20b-vector-rag" "gpt-oss:20b" "vector_only" "🔍 Vector RAG" \
    "純向量檢索，20B參數，適合語義相似性查詢和創意分析"

create_rag_model "gpt-oss-20b-graph-rag" "gpt-oss:20b" "graph_only" "🕸️ Graph RAG" \
    "知識圖譜檢索，20B參數，適合探索藝術家和作品的關係網絡"

create_rag_model "gpt-oss-20b-advanced-rag" "gpt-oss:20b" "advanced_rag" "🎯 Advanced RAG" \
    "多級檢索與重排序，20B參數，適合深度研究和比較分析"

create_rag_model "gpt-oss-20b-agentic-rag" "gpt-oss:20b" "agentic_rag" "🤖 Agentic RAG" \
    "智能代理式推理，20B參數，適合需要多步驟邏輯推理的複雜問題"

create_rag_model "gpt-oss-20b-self-rag" "gpt-oss:20b" "self_rag" "🔄 Self RAG" \
    "自我反思策略，20B參數，適合需要高準確性的學術查詢"

create_rag_model "gpt-oss-20b-naive-rag" "gpt-oss:20b" "naive_rag" "⚡ Naive RAG" \
    "極速檢索，20B參數，快速基礎問答"

echo "✅ GPT-OSS 20B 系列完成 (8個模型)"
echo ""

# ==================== DeepSeek-R1 32B 系列 ====================
echo "【2/4】創建 DeepSeek-R1 32B 系列..."
echo "-------------------------------------------"

create_rag_model "deepseek-32b-enhanced-rag" "deepseek-r1:32b" "enhanced_rag" "🌟 Enhanced RAG" \
    "雙資料庫檢索，32B參數超強推理，適合複雜學術研究"

create_rag_model "deepseek-32b-hybrid-rag" "deepseek-r1:32b" "hybrid_balanced" "⚖️ Hybrid RAG" \
    "平衡混合策略，32B參數專注推理，適合通用學術問答"

create_rag_model "deepseek-32b-vector-rag" "deepseek-r1:32b" "vector_only" "🔍 Vector RAG" \
    "純向量檢索，32B參數，適合需要深度邏輯分析的語義查詢"

create_rag_model "deepseek-32b-graph-rag" "deepseek-r1:32b" "graph_only" "🕸️ Graph RAG" \
    "知識圖譜檢索，32B參數推理專家，適合關係探索和結構化分析"

create_rag_model "deepseek-32b-advanced-rag" "deepseek-r1:32b" "advanced_rag" "🎯 Advanced RAG" \
    "多級檢索與重排序，32B參數，適合複雜的學術論證和比較研究"

create_rag_model "deepseek-32b-agentic-rag" "deepseek-r1:32b" "agentic_rag" "🤖 Agentic RAG" \
    "智能代理式推理，32B參數邏輯推理巔峰，適合多步驟複雜推理任務"

create_rag_model "deepseek-32b-self-rag" "deepseek-r1:32b" "self_rag" "🔄 Self RAG" \
    "自我反思策略，32B參數，適合需要自我驗證的高質量學術查詢"

create_rag_model "deepseek-32b-naive-rag" "deepseek-r1:32b" "naive_rag" "⚡ Naive RAG" \
    "極速檢索，32B參數，快速推理問答"

echo "✅ DeepSeek-R1 32B 系列完成 (8個模型)"
echo ""

# ==================== Qwen3 30B 系列 ====================
echo "【3/4】創建 Qwen3 30B 系列..."
echo "-------------------------------------------"

create_rag_model "qwen3-30b-enhanced-rag" "qwen3:30b" "enhanced_rag" "🌟 Enhanced RAG" \
    "雙資料庫檢索，30B參數頂級中文理解，適合複雜中文藝術史研究"

create_rag_model "qwen3-30b-hybrid-rag" "qwen3:30b" "hybrid_balanced" "⚖️ Hybrid RAG" \
    "平衡混合策略，30B參數中文優化，適合通用中文藝術史問答"

create_rag_model "qwen3-30b-vector-rag" "qwen3:30b" "vector_only" "🔍 Vector RAG" \
    "純向量檢索，30B參數，最強中文語義理解，適合中文相似性查詢"

create_rag_model "qwen3-30b-graph-rag" "qwen3:30b" "graph_only" "🕸️ Graph RAG" \
    "知識圖譜檢索，30B參數中文專精，適合中文藝術史關係探索"

create_rag_model "qwen3-30b-advanced-rag" "qwen3:30b" "advanced_rag" "🎯 Advanced RAG" \
    "多級檢索與重排序，30B參數，適合深度中文藝術史研究和文化分析"

create_rag_model "qwen3-30b-agentic-rag" "qwen3:30b" "agentic_rag" "🤖 Agentic RAG" \
    "智能代理式推理，30B參數中文優化，適合複雜中文邏輯推理"

create_rag_model "qwen3-30b-self-rag" "qwen3:30b" "self_rag" "🔄 Self RAG" \
    "自我反思策略，30B參數，適合需要高準確性的中文學術查詢"

create_rag_model "qwen3-30b-naive-rag" "qwen3:30b" "naive_rag" "⚡ Naive RAG" \
    "極速檢索，30B參數，快速中文問答"

echo "✅ Qwen3 30B 系列完成 (8個模型)"
echo ""

# ==================== Llama 3.1 70B 系列 ====================
echo "【4/4】創建 Llama 3.1 70B 系列..."
echo "-------------------------------------------"

create_rag_model "llama31-70b-enhanced-rag" "llama3.1:70b" "enhanced_rag" "🌟 Enhanced RAG" \
    "雙資料庫檢索，70B參數旗艦級，最強綜合能力，適合最複雜的藝術史研究"

create_rag_model "llama31-70b-hybrid-rag" "llama3.1:70b" "hybrid_balanced" "⚖️ Hybrid RAG" \
    "平衡混合策略，70B參數旗艦級，適合高質量通用問答"

create_rag_model "llama31-70b-vector-rag" "llama3.1:70b" "vector_only" "🔍 Vector RAG" \
    "純向量檢索，70B參數，最強語義理解和創意分析能力"

create_rag_model "llama31-70b-graph-rag" "llama3.1:70b" "graph_only" "🕸️ Graph RAG" \
    "知識圖譜檢索，70B參數旗艦級，最強關係推理和結構分析"

create_rag_model "llama31-70b-advanced-rag" "llama3.1:70b" "advanced_rag" "🎯 Advanced RAG" \
    "多級檢索與重排序，70B參數，適合最深度的研究和跨領域分析"

create_rag_model "llama31-70b-agentic-rag" "llama3.1:70b" "agentic_rag" "🤖 Agentic RAG" \
    "智能代理式推理，70B參數旗艦級，最強多步驟複雜推理能力"

create_rag_model "llama31-70b-self-rag" "llama3.1:70b" "self_rag" "🔄 Self RAG" \
    "自我反思策略，70B參數，最高質量學術查詢保證"

create_rag_model "llama31-70b-naive-rag" "llama3.1:70b" "naive_rag" "⚡ Naive RAG" \
    "極速檢索，70B參數，高質量快速問答"

echo "✅ Llama 3.1 70B 系列完成 (8個模型)"
echo ""

echo "==========================================="
echo "🎉 所有大型LLM+RAG組合模型創建完成！"
echo ""
echo "統計："
echo "- GPT-OSS 20B: 8個RAG組合"
echo "- DeepSeek-R1 32B: 8個RAG組合"
echo "- Qwen3 30B: 8個RAG組合"
echo "- Llama 3.1 70B: 8個RAG組合"
echo ""
echo "新增總計: 32個大型LLM+RAG組合模型"
echo "系統總計: 67個LLM+RAG組合模型 (原35個 + 新32個)"
echo "==========================================="
echo ""
echo "驗證新模型列表："
ollama list | grep -E "(gpt-oss-20b|deepseek-32b|qwen3-30b|llama31-70b)"

'

echo ""
echo "🎉 完成！現在請刷新OpenWebUI頁面查看新模型！"
echo ""
echo "💡 推薦的大型模型組合："
echo ""
echo "🏆 最強綜合能力："
echo "  llama31-70b-enhanced-rag - 70B旗艦級，雙資料庫全面檢索"
echo ""
echo "🧠 最強推理能力："
echo "  deepseek-32b-agentic-rag - 32B推理專家，智能代理推理"
echo ""
echo "🇨🇳 最強中文理解："
echo "  qwen3-30b-enhanced-rag - 30B中文專精，最佳中文語義"
echo ""
echo "🎨 最強創意分析："
echo "  gpt-oss-20b-advanced-rag - 20B創意模型，深度多級檢索"
echo ""
echo "📊 性能建議："
echo "  - 簡單問題: 使用 naive-rag 策略"
echo "  - 複雜研究: 使用 enhanced-rag 或 advanced-rag"
echo "  - 關係探索: 使用 graph-rag"
echo "  - 邏輯推理: 使用 agentic-rag (搭配 DeepSeek-32B)"
echo "  - 中文問題: 優先選擇 Qwen3-30B 系列"
echo ""
