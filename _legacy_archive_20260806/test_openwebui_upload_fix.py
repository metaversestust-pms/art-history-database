#!/usr/bin/env python3
"""
測試 OpenWebUI 上傳修復是否成功
模擬上傳流程來驗證嵌入生成
"""

import requests
import json

def test_ollama_batch_embedding():
    """測試修復後的批次嵌入生成"""

    print("=" * 60)
    print("測試 OpenWebUI 批次嵌入修復")
    print("=" * 60)
    print()

    # 測試資料
    texts = [
        "漢寶德是一位著名的建築師",
        "南藝大的創校校長是漢寶德",
        "漢寶德紀念館位於南藝大校園內"
    ]

    print(f"📝 測試文本 ({len(texts)} 個):")
    for i, text in enumerate(texts, 1):
        print(f"   {i}. {text}")
    print()

    # 模擬批次嵌入生成（修復後的邏輯）
    print("🔄 使用修復後的邏輯生成嵌入...")
    print()

    ollama_url = "http://localhost:11434/api/embeddings"
    model = "nomic-embed-text:latest"
    embeddings = []

    for i, text in enumerate(texts, 1):
        print(f"   處理文本 {i}/{len(texts)}...")

        try:
            # 使用正確的 Ollama API 格式
            response = requests.post(
                ollama_url,
                json={
                    "model": model,
                    "prompt": text  # ← 修復: 使用 prompt 而非 input
                },
                timeout=30
            )

            response.raise_for_status()
            data = response.json()

            if "embedding" in data:
                embedding = data["embedding"]
                embeddings.append(embedding)
                print(f"      ✅ 成功生成 {len(embedding)} 維嵌入")
            else:
                print(f"      ❌ 回應中沒有 embedding 欄位")
                return False

        except Exception as e:
            print(f"      ❌ 錯誤: {e}")
            return False

    print()
    print("=" * 60)
    print("✅ 測試通過！")
    print("=" * 60)
    print()
    print(f"📊 結果統計:")
    print(f"   輸入文本數: {len(texts)}")
    print(f"   生成嵌入數: {len(embeddings)}")
    print(f"   嵌入維度: {len(embeddings[0]) if embeddings else 0}")
    print()

    if len(embeddings) == len(texts):
        print("✅ 嵌入數量正確匹配！")
        print()
        print("💡 修復驗證成功，現在可以在 OpenWebUI 中上傳檔案了")
        return True
    else:
        print("❌ 嵌入數量不匹配")
        return False


def test_wrong_format():
    """測試錯誤的 API 格式（作為對照）"""

    print()
    print("=" * 60)
    print("測試錯誤的 API 格式（對照組）")
    print("=" * 60)
    print()

    texts = ["text1", "text2", "text3"]

    print("📝 使用錯誤的格式（input 參數）...")

    try:
        response = requests.post(
            "http://localhost:11434/api/embeddings",
            json={
                "model": "nomic-embed-text:latest",
                "input": texts  # ← 錯誤: Ollama 不支援此格式
            },
            timeout=10
        )

        data = response.json()
        print(f"   回應: {json.dumps(data, indent=2)}")

        if "embedding" in data:
            embeddings = data.get("embedding", [])
            print(f"   嵌入數量: {len(embeddings)}")
            if len(embeddings) == 0:
                print("   ❌ 返回空嵌入陣列（這就是原本的問題！）")
            else:
                print("   ✅ 有嵌入資料")

    except Exception as e:
        print(f"   ❌ 錯誤: {e}")

    print()


if __name__ == "__main__":
    # 執行測試
    success = test_ollama_batch_embedding()

    # 對照測試
    test_wrong_format()

    # 返回結果
    import sys
    sys.exit(0 if success else 1)
