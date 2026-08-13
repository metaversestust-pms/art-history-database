#!/usr/bin/env python3
"""
創建擴展的RAG模型組合 - 包含大型模型
為OpenWebUI創建9種LLM × 8種RAG = 72種組合的虛擬模型
"""

import subprocess
import time
import json
import sys

# 定義所有LLM模型
LLM_MODELS = {
    # 原有模型
    "gpt-oss:20b": "GPT-OSS 20B",
    "deepseek-r1:8b": "DeepSeek-R1 8B",
    "gemma3:1b": "Gemma3 1B",
    "qwen3:4b": "Qwen3 4B",
    "llama3.1:8b": "Llama 3.1 8B",
    # 新增大型模型
    "qwen3:30b": "Qwen3 30B",
    "deepseek-r1:32b": "DeepSeek-R1 32B",
    "llama3.1:70b": "Llama 3.1 70B",
}

# 定義所有RAG策略
RAG_STRATEGIES = {
    "enhanced_rag": "Enhanced RAG",
    "hybrid_balanced": "Hybrid RAG",
    "vector_only": "Vector RAG",
    "graph_only": "Graph RAG",
    "advanced_rag": "Advanced RAG",
    "agentic_rag": "Agentic RAG",
    "self_rag": "Self RAG",
    "naive_rag": "Naive RAG",
}

def create_modelfile_content(base_model: str, model_name: str, rag_strategy: str):
    """創建Modelfile內容"""
    return f"""FROM {base_model}

# 藝術史RAG+LLM組合模型
# LLM: {model_name}
# RAG策略: {rag_strategy}

PARAMETER temperature 0.1
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER num_predict 2048

SYSTEM \"\"\"
你是一位藝術史專家助手，結合了{rag_strategy}檢索策略。

你的特點：
1. 基於藝術史知識庫回答問題
2. 使用{rag_strategy}策略檢索相關資料
3. 提供準確、專業的藝術史資訊
4. 引用具體的藝術家、作品和歷史背景
5. 保持學術性和可讀性的平衡

當回答問題時：
- 優先使用知識庫中的資料
- 清晰標註資料來源
- 提供相關的歷史背景
- 必要時承認資訊不足
\"\"\"

TEMPLATE \"\"\"{{ if .System }}<|system|>
{{ .System }}<|end|>
{{ end }}{{ if .Prompt }}<|user|>
{{ .Prompt }}<|end|>
{{ end }}<|assistant|>
{{ .Response }}<|end|>
\"\"\"
"""

def create_rag_model(base_model: str, model_name: str, rag_strategy: str, rag_display_name: str):
    """創建單個RAG組合模型"""
    # 生成組合模型名稱
    safe_base = base_model.replace(":", "-").replace(".", "-")
    combo_name = f"{safe_base}-{rag_strategy}"

    print(f"\n{'='*60}")
    print(f"創建模型: {combo_name}")
    print(f"基礎模型: {base_model} ({model_name})")
    print(f"RAG策略: {rag_strategy} ({rag_display_name})")
    print(f"{'='*60}")

    # 創建Modelfile
    modelfile_content = create_modelfile_content(base_model, model_name, rag_display_name)

    try:
        # 使用stdin傳遞Modelfile內容
        result = subprocess.run(
            ["ollama", "create", combo_name, "-f", "-"],
            input=modelfile_content.encode(),
            capture_output=True,
            timeout=60
        )

        if result.returncode == 0:
            print(f"✅ 成功創建: {combo_name}")
            return True
        else:
            error_msg = result.stderr.decode() if result.stderr else "未知錯誤"
            print(f"❌ 創建失敗: {combo_name}")
            print(f"   錯誤: {error_msg}")
            return False

    except subprocess.TimeoutExpired:
        print(f"⏱️ 超時: {combo_name} (可能模型太大，仍在後台創建)")
        return False
    except Exception as e:
        print(f"❌ 異常: {combo_name}")
        print(f"   {str(e)}")
        return False

def check_base_model_exists(model_name: str) -> bool:
    """檢查基礎模型是否存在"""
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return model_name in result.stdout
    except:
        return False

def main():
    """主函數"""
    print("🎨 藝術史RAG模型組合創建工具 v5.0")
    print("="*60)
    print(f"將創建 {len(LLM_MODELS)} 種LLM × {len(RAG_STRATEGIES)} 種RAG = {len(LLM_MODELS) * len(RAG_STRATEGIES)} 種組合")
    print("="*60)

    # 檢查所有基礎模型
    print("\n📋 檢查基礎模型...")
    missing_models = []
    for model_id, model_name in LLM_MODELS.items():
        if check_base_model_exists(model_id):
            print(f"✅ {model_id} - {model_name}")
        else:
            print(f"❌ {model_id} - {model_name} (未安裝)")
            missing_models.append(model_id)

    if missing_models:
        print(f"\n⚠️ 警告: 以下模型未安裝，將跳過相關組合:")
        for model in missing_models:
            print(f"  - {model}")
        print("\n如需安裝，請執行:")
        for model in missing_models:
            print(f"  ollama pull {model}")

        response = input("\n是否繼續創建已安裝模型的組合? (y/n): ")
        if response.lower() != 'y':
            print("取消創建。")
            return

    # 創建所有組合
    print("\n🚀 開始創建模型組合...")
    created = 0
    failed = 0
    skipped = 0

    total = len(LLM_MODELS) * len(RAG_STRATEGIES)
    current = 0

    for model_id, model_name in LLM_MODELS.items():
        # 跳過未安裝的模型
        if model_id in missing_models:
            skipped += len(RAG_STRATEGIES)
            current += len(RAG_STRATEGIES)
            continue

        for rag_id, rag_name in RAG_STRATEGIES.items():
            current += 1
            print(f"\n[{current}/{total}] 處理中...")

            if create_rag_model(model_id, model_name, rag_id, rag_name):
                created += 1
            else:
                failed += 1

            # 短暫延遲避免資源耗盡
            time.sleep(0.5)

    # 總結
    print("\n" + "="*60)
    print("🎉 模型創建完成!")
    print("="*60)
    print(f"✅ 成功創建: {created} 個")
    print(f"❌ 創建失敗: {failed} 個")
    if skipped > 0:
        print(f"⏭️ 跳過: {skipped} 個")
    print(f"📊 總計: {total} 個組合")

    if created > 0:
        print("\n🎊 現在可以在OpenWebUI中使用這些組合了！")
        print("\n📝 使用方法:")
        print("1. 訪問 http://localhost:8080")
        print("2. 點擊左上角的模型選擇器")
        print("3. 搜索並選擇想要的組合，例如:")
        print("   - llama3-1-70b-enhanced_rag")
        print("   - qwen3-30b-vector_only")
        print("   - deepseek-r1-32b-advanced_rag")

    if failed > 0:
        print("\n⚠️ 部分模型創建失敗，可能原因:")
        print("  - 基礎模型未完全下載")
        print("  - 系統資源不足")
        print("  - Ollama服務異常")
        print("\n建議重新運行此腳本創建失敗的模型。")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ 用戶中斷，已取消創建。")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 程序異常: {str(e)}")
        sys.exit(1)
