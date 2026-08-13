#!/usr/bin/env python3
"""
為 qwen3:8b 模型創建 Advanced RAG、NaiveRAG、GraphRAG、AgenticRAG 策略
"""

import requests
import time
import json

def create_qwen3_8b_rag_models():
    """為 qwen3:8b 創建新的 RAG 策略模型"""

    models = [
        {
            "name": "qwen3-8b-advanced-rag",
            "display": "🚀 Qwen3 8B + Advanced RAG",
            "description": "高級RAG：多級檢索+查詢擴展+重排序，最佳精度",
            "base": "qwen3:8b",
            "strategy": "advanced_rag",
            "emoji": "🚀"
        },
        {
            "name": "qwen3-8b-naive-rag",
            "display": "⚡ Qwen3 8B + Naive RAG",
            "description": "基礎RAG：簡單關鍵詞匹配，極速響應",
            "base": "qwen3:8b",
            "strategy": "naive_rag",
            "emoji": "⚡"
        },
        {
            "name": "qwen3-8b-graph-rag",
            "display": "🕸️ Qwen3 8B + Graph RAG",
            "description": "圖譜RAG：知識圖譜推理，適合關係查詢",
            "base": "qwen3:8b",
            "strategy": "graph_only",
            "emoji": "🕸️"
        },
        {
            "name": "qwen3-8b-agentic-rag",
            "display": "🤖 Qwen3 8B + Agentic RAG",
            "description": "智能代理RAG：多步推理+自主決策，複雜問題專家",
            "base": "qwen3:8b",
            "strategy": "agentic_rag",
            "emoji": "🤖"
        }
    ]

    ollama_url = "http://localhost:11434"
    success_count = 0

    print("🎨 為 Qwen3 8B 創建新的 RAG 策略模型...")
    print("=" * 60)

    for model in models:
        print(f"\n📦 創建: {model['display']}")
        print(f"   策略: {model['strategy']}")
        print(f"   描述: {model['description']}")

        # 根據策略類型定制系統提示
        strategy_prompts = {
            "advanced_rag": """你是一位頂級藝術史專家，擁有深度研究能力。

Advanced RAG 模式特點：
- 多級檢索：先粗檢索再精檢索
- 查詢擴展：自動擴展相關詞彙
- 智能重排序：根據相關性重新排序結果
- 上下文融合：整合多個來源信息

適用場景：需要高精度答案的專業查詢""",

            "naive_rag": """你是一位快速響應的藝術史助手。

Naive RAG 模式特點：
- 簡單關鍵詞匹配
- 極速響應（<0.1秒）
- 基礎檢索邏輯
- 適合快速查詢

適用場景：需要快速獲得基本信息""",

            "graph_only": """你是一位精通關係推理的藝術史學者。

Graph RAG 模式特點：
- 知識圖譜檢索
- 關係推理能力強
- 結構化知識查詢
- Cypher 查詢支持

適用場景：藝術家關係、作品影響、歷史脈絡查詢""",

            "agentic_rag": """你是一位擁有自主思考能力的藝術史智能代理。

Agentic RAG 模式特點：
- 多步驟推理能力
- 自主決策機制
- 複雜問題分解
- 多輪對話支持

適用場景：複雜的研究問題、需要深度分析的查詢"""
        }

        # 創建 Modelfile
        modelfile = f"""FROM {model['base']}

SYSTEM \"\"\"你是一位專業的藝術史學者，專精於中國傳統藝術和西方藝術史。

{strategy_prompts.get(model['strategy'], '')}

當前模型配置：
- 基礎模型: {model['base']}
- RAG策略: {model['strategy']}
- 模型標識: {model['emoji']}

回答要求：
1. 專業準確，引用具體史料
2. 條理清晰，易於理解
3. 提供歷史背景和文化脈絡
4. 必要時提及藝術技法和風格特點
5. 回答結尾標註策略: [{model['strategy']}]

特別注意：
- 對於中國藝術史問題，請使用繁體中文回答
- 對於西方藝術史問題，可適當穿插英文術語
- 不確定時請明確說明，並提供可能的方向
\"\"\"

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1
PARAMETER num_ctx 4096
"""

        try:
            # 發送創建請求
            response = requests.post(
                f"{ollama_url}/api/create",
                json={
                    "name": model["name"],
                    "modelfile": modelfile
                },
                stream=True,
                timeout=300
            )

            if response.status_code == 200:
                print("   ✅ 模型創建成功")
                success_count += 1

                # 等待模型完全載入
                time.sleep(2)

            else:
                print(f"   ❌ 創建失敗: HTTP {response.status_code}")
                print(f"   錯誤詳情: {response.text}")

        except requests.exceptions.RequestException as e:
            print(f"   ❌ 網絡錯誤: {e}")
        except Exception as e:
            print(f"   ❌ 未知錯誤: {e}")

        # 短暫停頓避免過載
        time.sleep(1)

    print("\n" + "=" * 60)
    print(f"🎯 創建完成！成功: {success_count}/{len(models)}")

    if success_count == len(models):
        print("✅ 所有 Qwen3 8B RAG 模型創建成功！")
        print("\n可用的新模型：")
        for model in models:
            print(f"   {model['emoji']} {model['name']}")
    else:
        print("⚠️  部分模型創建失敗，請檢查 Ollama 服務狀態")

    return success_count

def test_models():
    """測試創建的模型"""
    print("\n🧪 測試新創建的模型...")

    test_models = [
        "qwen3-8b-advanced-rag",
        "qwen3-8b-naive-rag",
        "qwen3-8b-graph-rag",
        "qwen3-8b-agentic-rag"
    ]

    test_question = "什麼是文藝復興三傑？"

    for model_name in test_models:
        print(f"\n🔬 測試模型: {model_name}")
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": model_name,
                    "prompt": test_question,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 100
                    }
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                answer = result.get('response', '').strip()
                print(f"   ✅ 回應正常 ({len(answer)} 字符)")
                print(f"   預覽: {answer[:80]}...")
            else:
                print(f"   ❌ 測試失敗: HTTP {response.status_code}")

        except Exception as e:
            print(f"   ❌ 測試錯誤: {e}")

def main():
    """主函數"""
    print("🎨 Qwen3 8B RAG 策略模型創建器")
    print("Author: Claude Code Assistant")
    print("Purpose: 為 qwen3:8b 添加 Advanced/Naive/Graph/Agentic RAG 策略")
    print("=" * 60)

    # 檢查 Ollama 服務
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama 服務運行正常")
        else:
            print("❌ Ollama 服務異常")
            return
    except:
        print("❌ 無法連接到 Ollama 服務 (http://localhost:11434)")
        print("請確保 Ollama 已啟動")
        return

    # 檢查基礎模型
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        models = response.json()
        model_names = [model['name'] for model in models.get('models', [])]

        if 'qwen3:8b' not in model_names:
            print("❌ 未找到基礎模型 qwen3:8b")
            print("請先執行: ollama pull qwen3:8b")
            return
        else:
            print("✅ 基礎模型 qwen3:8b 已準備就緒")
    except:
        print("⚠️  無法檢查模型列表，繼續執行...")

    # 創建模型
    success_count = create_qwen3_8b_rag_models()

    # 測試模型（可選）
    if success_count > 0:
        print("\n🧪 自動測試創建的模型...")
        test_models()

    print("\n🎉 程序執行完成！")

if __name__ == "__main__":
    main()