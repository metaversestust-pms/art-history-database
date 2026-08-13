#!/usr/bin/env python3
"""
創建Advanced RAG和SelfRAG與gpt-oss:20b的組合模型
"""

import os
import time
import subprocess

def create_advanced_rag_models():
    """創建新的Advanced RAG+LLM組合模型"""

    # 包含所有現有模型的Advanced RAG和SelfRAG變體
    base_models = [
        {"name": "gpt-oss:20b", "display": "GPT-OSS 20B"},
        {"name": "llama3.1:8b", "display": "Llama 3.1 8B"},
        {"name": "qwen3:4b", "display": "Qwen3 4B"}
    ]

    advanced_strategies = [
        {
            "strategy": "advanced_rag",
            "display_name": "Advanced RAG",
            "emoji": "🚀",
            "description": "多級檢索與重排序，包含查詢擴展"
        },
        {
            "strategy": "self_rag",
            "display_name": "Self-RAG",
            "emoji": "🧠",
            "description": "自我反思策略，具備質量評估和迭代改進"
        }
    ]

    models = []

    # 為每個基礎模型創建Advanced策略的組合
    for base in base_models:
        for strategy in advanced_strategies:
            model_name = f"{base['name'].replace(':', '-').replace('.', '')}-{strategy['strategy'].replace('_', '-')}"
            models.append({
                "name": model_name,
                "display": f"{strategy['emoji']} {base['display']} + {strategy['display_name']}",
                "description": f"{strategy['description']}，基於{base['display']}",
                "base": base['name'],
                "strategy": strategy['strategy']
            })

    success_count = 0

    print("🎨 創建Advanced RAG+LLM組合模型...")
    print(f"📊 計劃創建 {len(models)} 個模型")

    for i, model in enumerate(models, 1):
        print(f"📦 [{i}/{len(models)}] 創建: {model['display']}")

        # 創建Modelfile
        modelfile_content = f"""FROM {model['base']}

SYSTEM \"\"\"你是一位專業的藝術史學者，專精於中國傳統藝術和西方藝術史。

當前RAG策略: {model['strategy']}
基礎模型: {model['base']}
策略描述: {model['description']}

你使用的是{model['strategy']}策略，這意味著：
- 如果是advanced_rag：你會進行多級檢索、查詢擴展和結果重排序
- 如果是self_rag：你會進行自我評估、質量反思和迭代改進

請根據知識庫內容專業地回答藝術史相關問題。充分利用你的策略特性提供高質量回答。

回答要求：
1. 專業準確，體現策略特色
2. 易於理解，結構清晰
3. 提供豐富的歷史背景
4. 適當引用相關資料來源
5. 在回答結尾註明使用策略: {model['strategy']}

如果使用Advanced RAG，請展示多角度分析；
如果使用Self-RAG，請體現反思性思考過程。
\"\"\"

PARAMETER temperature 0.1
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1
PARAMETER num_ctx 4096"""

        # 將Modelfile寫入臨時文件
        temp_file = f"/tmp/claude/{model['name']}.modelfile"
        os.makedirs("/tmp/claude", exist_ok=True)

        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(modelfile_content)

        try:
            # 使用命令行創建模型
            result = subprocess.run([
                "ollama", "create", model['name'], "-f", temp_file
            ], capture_output=True, text=True, timeout=180)

            if result.returncode == 0:
                print(f"   ✅ 成功創建: {model['name']}")
                success_count += 1
            else:
                print(f"   ❌ 創建失敗: {model['name']}")
                print(f"   錯誤: {result.stderr}")

        except subprocess.TimeoutExpired:
            print(f"   ⏰ 創建超時: {model['name']}")
        except Exception as e:
            print(f"   ❌ 創建異常: {model['name']} - {e}")

        # 清理臨時文件
        try:
            os.remove(temp_file)
        except:
            pass

        # 添加短暫延遲
        time.sleep(1)

    print(f"\n🎉 模型創建完成！成功: {success_count}/{len(models)}")

    # 顯示創建的模型列表
    print("\n📋 已創建的Advanced RAG模型:")
    subprocess.run(["ollama", "list"], check=False)

    return success_count

if __name__ == "__main__":
    create_advanced_rag_models()