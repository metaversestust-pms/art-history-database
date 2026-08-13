#!/bin/bash

# 將 RAG+LLM 策略註冊為 Ollama 模型
# 這樣就可以在 OpenWebUI 中直接選擇使用

echo "🎨 藝術史 RAG+LLM 策略模型註冊工具"
echo "========================================"
echo ""

# 定義 RAG 策略
RAG_STRATEGIES=(
    "vector_rag:ChromaDB向量檢索"
    "graph_rag:Neo4j圖譜檢索"
    "hybrid_rag:混合檢索"
    "enhanced_rag:增強型檢索"
    "advanced_rag:高級檢索"
    "agentic_rag:智能代理檢索"
    "self_rag:自我反思檢索"
    "naive_rag:快速檢索"
)

# 定義基礎 LLM 模型
BASE_MODELS=(
    "llama3.1:8b"
    "qwen2.5:7b"
    "gemma2:2b"
)

echo "📊 將創建以下 RAG+LLM 組合模型:"
echo ""

# 計算總數
TOTAL_COMBINATIONS=$((${#RAG_STRATEGIES[@]} * ${#BASE_MODELS[@]}))
echo "總共: $TOTAL_COMBINATIONS 個組合"
echo ""

CREATED=0
FAILED=0

# 為每個組合創建 Modelfile
for base_model in "${BASE_MODELS[@]}"; do
    # 提取模型名稱（去除版本號）
    model_name=$(echo $base_model | cut -d':' -f1)

    for strategy in "${RAG_STRATEGIES[@]}"; do
        # 分離策略名稱和描述
        strategy_name=$(echo $strategy | cut -d':' -f1)
        strategy_desc=$(echo $strategy | cut -d':' -f2)

        # 創建組合模型名稱
        combined_name="${model_name}-${strategy_name}"

        echo "🔧 創建模型: $combined_name"

        # 創建 Modelfile
        cat > "/tmp/${combined_name}.Modelfile" << EOF
FROM $base_model

# RAG+LLM 組合模型
# 基礎模型: $base_model
# RAG 策略: $strategy_name ($strategy_desc)

# 系統提示詞
SYSTEM """
你是一個藝術史專家助手，專注於提供準確、詳細的藝術史知識。

當前配置:
- 基礎 LLM: $base_model
- RAG 策略: $strategy_name
- RAG 描述: $strategy_desc

你會使用 RAG 檢索系統從以下來源獲取信息:
- Neo4j 知識圖譜（藝術家、作品、流派關係）
- ChromaDB 向量資料庫（1,441 件作品，95.5% 中文標籤）

回答時請:
1. 基於檢索到的資料提供準確答案
2. 引用具體的藝術家、作品名稱
3. 如果資料不足，誠實說明
4. 使用清晰、專業的語言
"""

# 參數設置
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40

# Modelfile 模板
TEMPLATE """{{ if .System }}<|system|>
{{ .System }}<|end|>
{{ end }}{{ if .Prompt }}<|user|>
{{ .Prompt }}<|end|>
{{ end }}<|assistant|>
{{ .Response }}<|end|>
"""
EOF

        # 使用 Docker 執行創建模型
        docker exec art-history-ollama ollama create "$combined_name" -f "/tmp/${combined_name}.Modelfile" > /dev/null 2>&1

        if [ $? -eq 0 ]; then
            echo "  ✅ 成功"
            ((CREATED++))
        else
            echo "  ❌ 失敗"
            ((FAILED++))
        fi

        # 清理臨時文件
        rm -f "/tmp/${combined_name}.Modelfile"
    done
    echo ""
done

echo "========================================"
echo "📊 註冊結果:"
echo "  ✅ 成功: $CREATED 個"
echo "  ❌ 失敗: $FAILED 個"
echo "  📦 總計: $TOTAL_COMBINATIONS 個"
echo ""

if [ $CREATED -gt 0 ]; then
    echo "🎉 模型已註冊！您現在可以在 OpenWebUI 中使用這些模型:"
    echo ""
    echo "在 OpenWebUI 的模型選擇下拉菜單中，您會看到:"
    echo "  - llama3.1-vector_rag (Llama 3.1 + ChromaDB向量檢索)"
    echo "  - llama3.1-graph_rag (Llama 3.1 + Neo4j圖譜檢索)"
    echo "  - qwen2.5-hybrid_rag (Qwen 2.5 + 混合檢索)"
    echo "  - ... 等共 $CREATED 個組合"
    echo ""
    echo "💡 使用方法:"
    echo "  1. 訪問 http://localhost:8080"
    echo "  2. 在模型選擇中選擇任一 RAG+LLM 組合"
    echo "  3. 開始提問藝術史問題！"
    echo ""
fi

echo "✅ 完成！"
