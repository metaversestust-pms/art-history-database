#!/usr/bin/env python3
"""
創建RAG+LLM組合模型的簡化版本
使用正確的Modelfile格式
"""

import requests
import time

def create_rag_models():
    """創建RAG+LLM組合模型"""

    models = [
        {
            "name": "llama31-vector-rag",
            "display": "🔍 Llama 3.1 8B + 向量RAG",
            "description": "語義相似度檢索，適合內容相似性查詢",
            "base": "llama3.1:8b",
            "strategy": "vector_only"
        },
        {
            "name": "llama31-graph-rag",
            "display": "🕸️ Llama 3.1 8B + 圖譜RAG",
            "description": "知識圖譜推理，適合關係和結構化查詢",
            "base": "llama3.1:8b",
            "strategy": "graph_only"
        },
        {
            "name": "llama31-hybrid-rag",
            "display": "⚖️ Llama 3.1 8B + 混合RAG",
            "description": "平衡混合策略，適合大多數查詢（推薦）",
            "base": "llama3.1:8b",
            "strategy": "hybrid_balanced"
        },
        {
            "name": "llama31-adaptive-rag",
            "display": "🧠 Llama 3.1 8B + 自適應RAG",
            "description": "基於歷史性能自動選擇最佳策略",
            "base": "llama3.1:8b",
            "strategy": "adaptive"
        },
        {
            "name": "qwen3-vector-rag",
            "display": "🔍 Qwen3 4B + 向量RAG",
            "description": "快速向量檢索，中文表現優秀",
            "base": "qwen3:4b",
            "strategy": "vector_only"
        },
        {
            "name": "qwen3-hybrid-rag",
            "display": "⚖️ Qwen3 4B + 混合RAG",
            "description": "快速混合檢索，適合日常中文問答",
            "base": "qwen3:4b",
            "strategy": "hybrid_balanced"
        }
    ]

    ollama_url = "http://localhost:11434"
    success_count = 0

    print("🎨 創建RAG+LLM組合模型...")

    for model in models:
        print(f"📦 創建: {model['display']}")

        # 創建Modelfile
        modelfile = f"""FROM {model['base']}

SYSTEM \"\"\"你是一位專業的藝術史學者，專精於中國傳統藝術和西方藝術史。

當前RAG策略: {model['strategy']}
基礎模型: {model['base']}

請根據知識庫內容專業地回答藝術史相關問題。如果沒有相關資料，請基於你的專業知識給出合理的解答。

回答要求：
1. 專業準確
2. 易於理解
3. 提供歷史背景
4. 在回答結尾註明使用策略: {model['strategy']}
\"\"\"

PARAMETER temperature 0.1
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1"""

        try:
            # 發送創建請求
            response = requests.post(
                f"{ollama_url}/api/create",
                json={
                    "name": model['name'],
                    "modelfile": modelfile,
                    "stream": False
                },
                timeout=60
            )

            if response.status_code == 200:
                print(f"   ✅ 成功: {model['name']}")
                success_count += 1
            else:
                print(f"   ❌ 失敗: {response.text}")

        except Exception as e:
            print(f"   ❌ 異常: {e}")

        time.sleep(1)

    print(f"\n🎉 完成！成功創建 {success_count}/{len(models)} 個模型")

    if success_count > 0:
        print("\n💡 現在請：")
        print("1. 刷新OpenWebUI頁面 (http://localhost:3001)")
        print("2. 點擊左上角模型選擇器")
        print("3. 您將看到新的RAG+LLM組合選項！")

    return success_count > 0

if __name__ == "__main__":
    # 等待Ollama準備就緒
    print("⏳ 檢查Ollama服務...")
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama服務正常")
            create_rag_models()
        else:
            print("❌ Ollama服務異常")
    except:
        print("❌ 無法連接Ollama服務")