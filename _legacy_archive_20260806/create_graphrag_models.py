#!/usr/bin/env python3
"""
為qwen3:4b和gpt-oss:20b創建GraphRAG組合模型
"""

import os
import time
import subprocess

def create_graphrag_models():
    """創建GraphRAG+LLM組合模型"""

    # 需要創建GraphRAG組合的基礎模型
    base_models = [
        {
            "name": "qwen3:4b",
            "display": "Qwen3 4B",
            "model_suffix": "qwen3-graph-rag"
        },
        {
            "name": "gpt-oss:20b",
            "display": "GPT-OSS 20B",
            "model_suffix": "gpt-oss-20b-graph-rag"
        }
    ]

    success_count = 0

    print("🕸️ 創建GraphRAG+LLM組合模型...")
    print(f"📊 計劃創建 {len(base_models)} 個GraphRAG模型")

    for i, base in enumerate(base_models, 1):
        print(f"📦 [{i}/{len(base_models)}] 創建: 🕸️ {base['display']} + GraphRAG")

        # 創建Modelfile
        modelfile_content = f"""FROM {base['name']}

SYSTEM \"\"\"你是一位專業的藝術史學者，專精於中國傳統藝術和西方藝術史。

當前RAG策略: graph_only
基礎模型: {base['name']}
策略描述: 純知識圖譜檢索，適合關係和結構化查詢

你使用的是graph_only策略，這意味著你專注於：
- 知識圖譜推理和結構化查詢
- 實體間的關係分析
- 藝術史中的時間脈絡和影響關係
- 藝術家、作品、流派之間的連結
- 歷史事件和藝術發展的因果關係

請根據知識庫內容專業地回答藝術史相關問題，充分利用知識圖譜的結構化特性。

回答要求：
1. 專業準確，突出關係和結構化分析
2. 易於理解，清晰展示實體關係
3. 提供豐富的歷史脈絡和連結
4. 善用圖譜數據展示藝術史發展軌跡
5. 在回答結尾註明使用策略: graph_only

特別強調實體關係、時間序列、影響傳承等圖譜特色內容。
\"\"\"

PARAMETER temperature 0.1
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1
PARAMETER num_ctx 4096"""

        # 將Modelfile寫入臨時文件
        temp_file = f"/tmp/claude/{base['model_suffix']}.modelfile"
        os.makedirs("/tmp/claude", exist_ok=True)

        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(modelfile_content)

        try:
            # 使用命令行創建模型
            result = subprocess.run([
                "ollama", "create", base['model_suffix'], "-f", temp_file
            ], capture_output=True, text=True, timeout=180)

            if result.returncode == 0:
                print(f"   ✅ 成功創建: {base['model_suffix']}")
                success_count += 1
            else:
                print(f"   ❌ 創建失敗: {base['model_suffix']}")
                print(f"   錯誤: {result.stderr}")

        except subprocess.TimeoutExpired:
            print(f"   ⏰ 創建超時: {base['model_suffix']}")
        except Exception as e:
            print(f"   ❌ 創建異常: {base['model_suffix']} - {e}")

        # 清理臨時文件
        try:
            os.remove(temp_file)
        except:
            pass

        # 添加短暫延遲
        time.sleep(1)

    print(f"\n🎉 GraphRAG模型創建完成！成功: {success_count}/{len(base_models)}")

    # 顯示創建的模型列表
    print("\n📋 已創建的GraphRAG模型:")
    subprocess.run(["ollama", "list"], check=False)

    return success_count

if __name__ == "__main__":
    create_graphrag_models()