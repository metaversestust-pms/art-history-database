#!/usr/bin/env python3
"""
恢復9/28的RAG+LLM組合模型
"""

import requests
import time
import sys

def create_rag_models():
    """創建RAG+LLM組合模型"""

    models = [
        {
            "name": "llama31-vector-rag",
            "display": "🔍 Llama 3.1 8B + 向量RAG",
            "base": "llama3.1:8b",
            "strategy": "vector_only"
        },
        {
            "name": "llama31-graph-rag",
            "display": "🕸️ Llama 3.1 8B + 圖譜RAG",
            "base": "llama3.1:8b",
            "strategy": "graph_only"
        },
        {
            "name": "llama31-hybrid-rag",
            "display": "⚖️ Llama 3.1 8B + 混合RAG",
            "base": "llama3.1:8b",
            "strategy": "hybrid_balanced"
        },
        {
            "name": "qwen3-vector-rag",
            "display": "🔍 Qwen3 4B + 向量RAG",
            "base": "qwen3:4b",
            "strategy": "vector_only"
        },
        {
            "name": "qwen3-hybrid-rag",
            "display": "⚖️ Qwen3 4B + 混合RAG",
            "base": "qwen3:4b",
            "strategy": "hybrid_balanced"
        },
        {
            "name": "qwen3-8b-graph-rag",
            "display": "🕸️ Qwen3 8B + Graph RAG",
            "base": "qwen3:8b",
            "strategy": "graph_only"
        }
    ]

    ollama_url = "http://localhost:11434"
    success_count = 0

    print("🎨 開始創建RAG+LLM組合模型...")
    print("=" * 60)

    for i, model in enumerate(models, 1):
        print(f"\n[{i}/{len(models)}] 📦 創建: {model['display']}")
        print(f"   ID: {model['name']}")
        print(f"   策略: {model['strategy']}")

        # 創建Modelfile
        modelfile = f"""FROM {model['base']}

SYSTEM \"\"\"你是一位專業的藝術史學者，專精於中國傳統藝術和西方藝術史。

當前配置：
- RAG策略: {model['strategy']}
- 基礎模型: {model['base']}
- 組合ID: {model['name']}

請根據知識庫內容專業地回答藝術史相關問題。

回答要求：
1. 專業準確，引用具體史料
2. 條理清晰，易於理解
3. 提供歷史背景和文化脈絡
4. 必要時提及藝術技法和風格特點
\"\"\"

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1
PARAMETER num_ctx 4096
"""

        try:
            response = requests.post(
                f"{ollama_url}/api/create",
                json={
                    "name": model['name'],
                    "modelfile": modelfile
                },
                stream=True,
                timeout=120
            )

            if response.status_code == 200:
                print(f"   ✅ 創建成功")
                success_count += 1
            else:
                print(f"   ❌ 創建失敗: {response.status_code}")
                print(f"   錯誤: {response.text}")

        except Exception as e:
            print(f"   ❌ 異常: {e}")

        time.sleep(2)

    print("\n" + "=" * 60)
    print(f"🎉 完成！成功創建 {success_count}/{len(models)} 個模型")

    if success_count == len(models):
        print("\n✅ 所有RAG組合模型創建成功！")
        print("\n可用的RAG+LLM組合：")
        for model in models:
            print(f"   {model['display']}")
        return True
    else:
        print("\n⚠️  部分模型創建失敗")
        return False

def verify_models():
    """驗證模型創建成功"""
    print("\n🔍 驗證模型...")

    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [m['name'] for m in models]

            rag_models = [name for name in model_names if 'rag' in name]

            print(f"\n找到 {len(rag_models)} 個RAG組合模型：")
            for name in rag_models:
                print(f"   ✅ {name}")

            return len(rag_models) > 0
        else:
            print("❌ 無法獲取模型列表")
            return False

    except Exception as e:
        print(f"❌ 驗證失敗: {e}")
        return False

if __name__ == "__main__":
    print("🎨 RAG+LLM組合模型恢復工具")
    print("Author: Art History Database Team")
    print("Purpose: 恢復9/28的完整RAG系統配置")
    print("=" * 60)

    # 檢查Ollama服務
    print("\n⏳ 檢查Ollama服務...")
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama服務運行正常")
        else:
            print("❌ Ollama服務異常")
            sys.exit(1)
    except:
        print("❌ 無法連接到Ollama服務")
        print("請確保Ollama容器正在運行：docker ps | grep ollama")
        sys.exit(1)

    # 創建模型
    success = create_rag_models()

    if success:
        # 驗證
        verify_models()

        print("\n" + "=" * 60)
        print("🎉 RAG+LLM組合模型恢復完成！")
        print("\n📝 下一步操作：")
        print("1. 刷新OpenWebUI頁面 (http://localhost:8080)")
        print("2. 點擊左上角的模型選擇器")
        print("3. 你應該能看到所有RAG組合模型了！")
        print("\n如果需要RAG功能，還需要：")
        print("4. 在OpenWebUI中啟用Functions功能")
        print("5. 上傳 enhanced_openwebui_rag_function_v3.py")
    else:
        print("\n❌ 部分模型創建失敗，請檢查錯誤信息")
        sys.exit(1)
