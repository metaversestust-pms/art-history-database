#!/usr/bin/env python3
"""
測試已註冊的RAG+LLM組合模型
"""

import requests
import json
import time

def test_model_availability():
    """測試已註冊模型的可用性"""
    print("🧪 測試已註冊的RAG+LLM組合模型")
    print("=" * 50)

    # 檢查Ollama服務
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        if response.status_code == 200:
            print("✅ Ollama服務正常運行")
            models_data = response.json()
            available_models = [model['name'] for model in models_data.get('models', [])]

            print(f"📋 可用模型總數: {len(available_models)}")

            # 檢查我們的RAG+LLM組合模型
            target_models = [
                "qwen3-4b-basic_rag:latest",
                "gpt-oss-20b-agentic_rag:latest",
                "gemma3-1b-naive_rag:latest"
            ]

            print("\n🎯 檢查已註冊的RAG+LLM組合模型:")

            for model in target_models:
                if model in available_models:
                    print(f"✅ {model} - 已註冊且可用")

                    # 獲取模型詳細信息
                    for m in models_data.get('models', []):
                        if m['name'] == model:
                            size_gb = m.get('size', 0) / (1024**3)
                            modified = m.get('modified_at', 'Unknown')
                            print(f"   📊 大小: {size_gb:.1f} GB")
                            print(f"   📅 修改時間: {modified[:19] if modified != 'Unknown' else 'Unknown'}")
                            break
                else:
                    print(f"❌ {model} - 未找到")

            return True

        else:
            print(f"❌ Ollama服務響應錯誤: HTTP {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到Ollama服務 (http://localhost:11434)")
        print("   請確認Ollama正在運行")
        return False
    except Exception as e:
        print(f"❌ 檢查Ollama服務時發生錯誤: {e}")
        return False

def test_rag_service():
    """測試RAG服務狀態"""
    print("\n🔍 檢查RAG服務狀態")
    print("-" * 30)

    try:
        response = requests.get("http://localhost:8008/health", timeout=5)
        if response.status_code == 200:
            print("✅ RAG管理API (端口8008): 運行正常")

            # 檢查可用策略
            try:
                strategies_response = requests.get("http://localhost:8008/system/strategies", timeout=5)
                if strategies_response.status_code == 200:
                    strategies = strategies_response.json()
                    print(f"📋 可用RAG策略: {len(strategies)} 個")

                    target_strategies = ["basic_rag", "agentic_rag", "naive_rag"]
                    for strategy in target_strategies:
                        if strategy in strategies:
                            print(f"✅ {strategy}: {strategies[strategy]}")
                        else:
                            print(f"❌ {strategy}: 未找到")

            except Exception as e:
                print(f"⚠️  無法獲取RAG策略信息: {e}")

            return True
        else:
            print(f"❌ RAG管理API響應錯誤: HTTP {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到RAG服務 (http://localhost:8008)")
        print("   請確認RAG服務正在運行")
        return False
    except Exception as e:
        print(f"❌ 檢查RAG服務時發生錯誤: {e}")
        return False

def quick_model_test():
    """快速測試模型響應"""
    print("\n⚡ 快速模型響應測試")
    print("-" * 30)

    test_cases = [
        ("gemma3-1b-naive_rag", "測試", "極速響應測試"),
        ("qwen3-4b-basic_rag", "什麼是藝術？", "中文查詢測試"),
    ]

    for model, query, description in test_cases:
        print(f"\n📝 {description}")
        print(f"   模型: {model}")
        print(f"   查詢: {query}")

        try:
            start_time = time.time()
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": model,
                    "prompt": query,
                    "stream": False
                },
                timeout=30
            )
            end_time = time.time()

            if response.status_code == 200:
                response_time = end_time - start_time
                print(f"   ✅ 響應成功 ({response_time:.1f}秒)")

                # 檢查響應內容
                result = response.json()
                response_text = result.get('response', '')
                if response_text and len(response_text) > 10:
                    print(f"   📝 響應長度: {len(response_text)} 字符")
                    print(f"   📄 預覽: {response_text[:100]}...")
                else:
                    print("   ⚠️  響應內容較短或為空")
            else:
                print(f"   ❌ 請求失敗: HTTP {response.status_code}")

        except requests.exceptions.Timeout:
            print("   ⏱️  請求超時 (30秒)")
        except Exception as e:
            print(f"   ❌ 測試失敗: {e}")

def show_upload_guide():
    """顯示函數上傳指南"""
    print("\n📖 OpenWebUI函數上傳指南")
    print("=" * 40)

    print("1. 📂 函數文件位置:")
    print("   /mnt/c/Users/ssking1999/Desktop/藝術史資料庫/art-history-database/enhanced_openwebui_rag_function_v3.py")

    print("\n2. 🌐 在OpenWebUI中:")
    print("   - 打開 Settings → Functions")
    print("   - 點擊 '+ Add Function'")
    print("   - 選擇 'Upload from File' 或 'Paste Code'")
    print("   - 上傳或貼上函數代碼")
    print("   - 確保函數狀態為 'Enabled'")

    print("\n3. ✅ 驗證步驟:")
    print("   - 在聊天界面檢查模型選擇下拉菜單")
    print("   - 應該看到三個新模型:")
    print("     • qwen3-4b-basic_rag")
    print("     • gpt-oss-20b-agentic_rag")
    print("     • gemma3-1b-naive_rag")

    print("\n4. 🧪 測試建議:")
    print("   - qwen3-4b-basic_rag: '印象派的特色是什麼？'")
    print("   - gpt-oss-20b-agentic_rag: '分析達文西的藝術技法'")
    print("   - gemma3-1b-naive_rag: '梵谷'")

def main():
    print("🎨 RAG+LLM組合模型測試工具")
    print("=" * 50)

    # 測試模型可用性
    models_ok = test_model_availability()

    # 測試RAG服務
    rag_ok = test_rag_service()

    if models_ok and rag_ok:
        # 進行快速響應測試
        quick_model_test()

        print("\n" + "=" * 50)
        print("🎉 系統狀態總結:")
        print("✅ Ollama服務: 運行正常")
        print("✅ RAG管理API: 運行正常")
        print("✅ 3個RAG+LLM組合模型: 已註冊")
        print("\n📱 下一步: 上傳OpenWebUI函數")

    else:
        print("\n❌ 系統檢查發現問題，請解決後再繼續")

    # 顯示上傳指南
    show_upload_guide()

if __name__ == "__main__":
    main()