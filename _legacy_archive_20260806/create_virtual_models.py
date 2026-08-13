#!/usr/bin/env python3
"""
為OpenWebUI創建虛擬RAG+LLM組合模型
通過OpenWebUI API註冊自定義模型組合
"""

import requests
import json
import time


class VirtualModelCreator:
    def __init__(self):
        self.openwebui_url = "http://localhost:3001"
        self.models = [
            {
                "id": "llama31_vector_rag",
                "name": "🔍 Llama 3.1 8B + 向量RAG",
                "description": "語義相似度檢索，適合內容相似性查詢",
                "owned_by": "custom",
                "meta": {
                    "base_model": "llama3.1:8b",
                    "rag_strategy": "vector_only",
                    "temperature": 0.1,
                    "max_tokens": 2048
                }
            },
            {
                "id": "llama31_graph_rag",
                "name": "🕸️ Llama 3.1 8B + 圖譜RAG",
                "description": "知識圖譜推理，適合關係和結構化查詢",
                "owned_by": "custom",
                "meta": {
                    "base_model": "llama3.1:8b",
                    "rag_strategy": "graph_only",
                    "temperature": 0.1,
                    "max_tokens": 2048
                }
            },
            {
                "id": "llama31_hybrid_rag",
                "name": "⚖️ Llama 3.1 8B + 混合RAG",
                "description": "平衡混合策略，適合大多數查詢（推薦）",
                "owned_by": "custom",
                "meta": {
                    "base_model": "llama3.1:8b",
                    "rag_strategy": "hybrid_balanced",
                    "temperature": 0.1,
                    "max_tokens": 2048
                }
            },
            {
                "id": "llama31_adaptive_rag",
                "name": "🧠 Llama 3.1 8B + 自適應RAG",
                "description": "基於歷史性能自動選擇最佳策略",
                "owned_by": "custom",
                "meta": {
                    "base_model": "llama3.1:8b",
                    "rag_strategy": "adaptive",
                    "temperature": 0.1,
                    "max_tokens": 2048
                }
            },
            {
                "id": "llama31_specialized_rag",
                "name": "🎯 Llama 3.1 8B + 專門RAG",
                "description": "基於查詢類型自動選擇專門策略",
                "owned_by": "custom",
                "meta": {
                    "base_model": "llama3.1:8b",
                    "rag_strategy": "specialized",
                    "temperature": 0.1,
                    "max_tokens": 2048
                }
            },
            {
                "id": "qwen3_vector_rag",
                "name": "🔍 Qwen3 4B + 向量RAG",
                "description": "快速向量檢索，中文表現優秀",
                "owned_by": "custom",
                "meta": {
                    "base_model": "qwen3:4b",
                    "rag_strategy": "vector_only",
                    "temperature": 0.2,
                    "max_tokens": 1500
                }
            },
            {
                "id": "qwen3_hybrid_rag",
                "name": "⚖️ Qwen3 4B + 混合RAG",
                "description": "快速混合檢索，適合日常中文問答",
                "owned_by": "custom",
                "meta": {
                    "base_model": "qwen3:4b",
                    "rag_strategy": "hybrid_balanced",
                    "temperature": 0.2,
                    "max_tokens": 1500
                }
            },
            {
                "id": "llama31_pure",
                "name": "💬 Llama 3.1 8B (純模型)",
                "description": "不使用RAG，僅基於預訓練知識",
                "owned_by": "custom",
                "meta": {
                    "base_model": "llama3.1:8b",
                    "rag_strategy": "none",
                    "temperature": 0.3,
                    "max_tokens": 2048
                }
            },
            {
                "id": "qwen3_pure",
                "name": "💬 Qwen3 4B (純模型)",
                "description": "不使用RAG，快速基礎對話",
                "owned_by": "custom",
                "meta": {
                    "base_model": "qwen3:4b",
                    "rag_strategy": "none",
                    "temperature": 0.4,
                    "max_tokens": 1500
                }
            }
        ]

    def wait_for_openwebui(self, max_wait=60):
        """等待OpenWebUI啟動"""
        print("⏳ 等待OpenWebUI啟動...")
        start_time = time.time()

        while time.time() - start_time < max_wait:
            try:
                response = requests.get(f"{self.openwebui_url}/health", timeout=5)
                if response.status_code == 200:
                    print("✅ OpenWebUI已啟動")
                    return True
            except:
                pass
            time.sleep(2)

        print("❌ 等待OpenWebUI超時")
        return False

    def create_modelfile(self, model_data):
        """為每個RAG組合創建Modelfile"""
        base_model = model_data["meta"]["base_model"]
        rag_strategy = model_data["meta"]["rag_strategy"]

        modelfile = f"""FROM {base_model}

# RAG增強系統提示詞
SYSTEM \"\"\"
你是一位專業的藝術史學者，專精於中國傳統藝術和西方藝術史。

當前使用的RAG策略: {rag_strategy}
當前基礎模型: {base_model}

請根據提供的知識庫內容回答用戶的藝術史相關問題，如果沒有相關資料，請基於你的專業知識給出合理的解答。

回答要求：
1. 專業準確
2. 易於理解
3. 提供歷史背景
4. 如有需要，提及相關藝術家或作品

在回答結尾請註明使用的RAG策略：{rag_strategy.replace('_', ' ').title()}
\"\"\"

# 參數設定
PARAMETER temperature {model_data["meta"]["temperature"]}
PARAMETER num_predict {model_data["meta"]["max_tokens"]}
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1

# 模型標籤
TEMPLATE \"\"\"{{ if .System }}<|start_header_id|>system<|end_header_id|>

{{ .System }}<|eot_id|>{{ end }}{{ if .Prompt }}<|start_header_id|>user<|end_header_id|>

{{ .Prompt }}<|eot_id|>{{ end }}<|start_header_id|>assistant<|end_header_id|>

\"\"\"
"""
        return modelfile

    def create_model_via_ollama(self, model_data):
        """通過Ollama API創建模型"""
        try:
            modelfile = self.create_modelfile(model_data)

            response = requests.post(
                "http://localhost:11434/api/create",
                json={
                    "name": model_data["id"],
                    "modelfile": modelfile,
                    "stream": False
                },
                timeout=120
            )

            if response.status_code == 200:
                print(f"✅ 已創建模型: {model_data['name']}")
                return True
            else:
                print(f"❌ 創建模型失敗 {model_data['name']}: {response.text}")
                return False

        except Exception as e:
            print(f"❌ 創建模型異常 {model_data['name']}: {e}")
            return False

    def create_all_models(self):
        """創建所有RAG+LLM組合模型"""
        if not self.wait_for_openwebui():
            return False

        print("🚀 開始創建RAG+LLM組合模型...")

        success_count = 0
        for model_data in self.models:
            print(f"📦 創建模型: {model_data['name']}")
            if self.create_model_via_ollama(model_data):
                success_count += 1
            time.sleep(2)  # 避免請求過快

        print(f"\\n🎉 完成！成功創建 {success_count}/{len(self.models)} 個RAG+LLM組合模型")

        if success_count > 0:
            print("\\n💡 使用方式：")
            print("1. 刷新OpenWebUI頁面")
            print("2. 點擊左上角模型選擇器")
            print("3. 選擇任一RAG+LLM組合")
            print("4. 開始您的藝術史探索！")

        return success_count > 0

    def list_models(self):
        """列出所有定義的模型組合"""
        print("🎨 可用的RAG+LLM組合：\\n")
        for i, model in enumerate(self.models, 1):
            print(f"{i:2d}. {model['name']}")
            print(f"    📋 描述: {model['description']}")
            print(f"    🔧 基礎: {model['meta']['base_model']} + {model['meta']['rag_strategy']}")
            print()


def main():
    creator = VirtualModelCreator()

    print("🎨 藝術史RAG+LLM組合模型創建器")
    print("=" * 50)

    # 列出將要創建的模型
    creator.list_models()

    # 詢問用戶是否繼續
    response = input("是否要創建這些模型? (y/N): ")
    if response.lower() != 'y':
        print("取消創建")
        return

    # 創建模型
    success = creator.create_all_models()

    if success:
        print("\\n🎉 RAG+LLM組合模型創建完成！")
        print("現在您可以在OpenWebUI中選擇不同的組合了。")
    else:
        print("\\n❌ 模型創建失敗，請檢查Ollama和OpenWebUI服務狀態。")


if __name__ == "__main__":
    main()