#!/bin/bash
# 在Ollama容器內創建所有RAG組合模型

echo "🎨 創建所有RAG+LLM組合模型..."
echo "=========================================="

# 進入Ollama容器執行
docker exec art-history-ollama bash -c '

# Model 1: llama31-graph-rag
echo "[1/5] 創建 llama31-graph-rag..."
cat > /tmp/llama31-graph-rag.modelfile << "EOF"
FROM llama3.1:8b

SYSTEM """你是一位專業的藝術史學者，專精於中國傳統藝術和西方藝術史。

當前配置：
- RAG策略: graph_only (知識圖譜檢索)
- 基礎模型: llama3.1:8b
- 組合ID: llama31-graph-rag

特色：利用知識圖譜探索藝術概念間的深層關係，適合關係分析和結構化查詢。

請基於檢索到的藝術史知識，提供準確、詳細且富有洞察力的回答。
"""

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1
PARAMETER num_ctx 4096
EOF
ollama create llama31-graph-rag -f /tmp/llama31-graph-rag.modelfile

# Model 2: llama31-hybrid-rag
echo "[2/5] 創建 llama31-hybrid-rag..."
cat > /tmp/llama31-hybrid-rag.modelfile << "EOF"
FROM llama3.1:8b

SYSTEM """你是一位專業的藝術史學者，專精於中國傳統藝術和西方藝術史。

當前配置：
- RAG策略: hybrid_balanced (平衡混合策略)
- 基礎模型: llama3.1:8b
- 組合ID: llama31-hybrid-rag

特色：結合向量檢索和知識圖譜的優勢，適合大多數查詢場景（推薦使用）。

請基於檢索到的藝術史知識，提供準確、詳細且富有洞察力的回答。
"""

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1
PARAMETER num_ctx 4096
EOF
ollama create llama31-hybrid-rag -f /tmp/llama31-hybrid-rag.modelfile

# Model 3: qwen3-vector-rag
echo "[3/5] 創建 qwen3-vector-rag..."
cat > /tmp/qwen3-vector-rag.modelfile << "EOF"
FROM qwen3:4b

SYSTEM """你是一位專業的藝術史學者，專精於中國傳統藝術和西方藝術史。

當前配置：
- RAG策略: vector_only (純向量檢索)
- 基礎模型: qwen3:4b
- 組合ID: qwen3-vector-rag

特色：基於語義相似度的快速向量檢索，中文表現優秀，適合內容相似性查詢。

請基於檢索到的藝術史知識，提供準確、詳細且富有洞察力的回答。
"""

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1
PARAMETER num_ctx 4096
EOF
ollama create qwen3-vector-rag -f /tmp/qwen3-vector-rag.modelfile

# Model 4: qwen3-hybrid-rag
echo "[4/5] 創建 qwen3-hybrid-rag..."
cat > /tmp/qwen3-hybrid-rag.modelfile << "EOF"
FROM qwen3:4b

SYSTEM """你是一位專業的藝術史學者，專精於中國傳統藝術和西方藝術史。

當前配置：
- RAG策略: hybrid_balanced (平衡混合策略)
- 基礎模型: qwen3:4b
- 組合ID: qwen3-hybrid-rag

特色：快速混合檢索，適合日常中文問答，性能與準確性平衡。

請基於檢索到的藝術史知識，提供準確、詳細且富有洞察力的回答。
"""

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1
PARAMETER num_ctx 4096
EOF
ollama create qwen3-hybrid-rag -f /tmp/qwen3-hybrid-rag.modelfile

# Model 5: qwen3-8b-graph-rag
echo "[5/5] 創建 qwen3-8b-graph-rag..."
cat > /tmp/qwen3-8b-graph-rag.modelfile << "EOF"
FROM qwen3:8b

SYSTEM """你是一位專業的藝術史學者，專精於中國傳統藝術和西方藝術史。

當前配置：
- RAG策略: graph_only (知識圖譜檢索)
- 基礎模型: qwen3:8b
- 組合ID: qwen3-8b-graph-rag

特色：更大參數量配合知識圖譜推理，適合複雜的關係分析和深度查詢。

請基於檢索到的藝術史知識，提供準確、詳細且富有洞察力的回答。
"""

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1
PARAMETER num_ctx 4096
EOF
ollama create qwen3-8b-graph-rag -f /tmp/qwen3-8b-graph-rag.modelfile

echo ""
echo "=========================================="
echo "✅ 所有RAG模型創建完成！"
echo ""
echo "驗證模型列表："
ollama list | grep rag

'

echo ""
echo "🎉 完成！現在請刷新OpenWebUI頁面查看新模型！"
