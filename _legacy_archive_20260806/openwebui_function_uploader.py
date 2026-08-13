#!/usr/bin/env python3
"""
OpenWebUI函數自動上傳和測試工具
"""

import requests
import json
import time
import os
from pathlib import Path

class OpenWebUIUploader:
    def __init__(self, openwebui_url="http://localhost:3000"):
        self.base_url = openwebui_url
        self.session = requests.Session()

    def upload_function(self, function_file_path):
        """上傳函數到OpenWebUI"""
        print(f"🚀 開始上傳函數: {function_file_path}")

        if not os.path.exists(function_file_path):
            print(f"❌ 錯誤: 函數文件不存在: {function_file_path}")
            return False

        try:
            # 讀取函數文件內容
            with open(function_file_path, 'r', encoding='utf-8') as f:
                function_content = f.read()

            # 準備上傳數據
            upload_data = {
                "name": "enhanced_openwebui_rag_function_v3",
                "content": function_content,
                "type": "function"
            }

            # 嘗試通過API上傳
            upload_url = f"{self.base_url}/api/v1/functions/import"

            print(f"📤 正在上傳到: {upload_url}")

            response = self.session.post(
                upload_url,
                json=upload_data,
                headers={
                    "Content-Type": "application/json"
                }
            )

            if response.status_code == 200:
                print("✅ 函數上傳成功！")
                return True
            else:
                print(f"❌ 上傳失敗: HTTP {response.status_code}")
                print(f"   響應: {response.text}")
                return False

        except Exception as e:
            print(f"❌ 上傳過程中發生錯誤: {e}")
            return False

    def list_functions(self):
        """列出所有已上傳的函數"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/functions")
            if response.status_code == 200:
                functions = response.json()
                print(f"📋 已上傳的函數 ({len(functions)} 個):")
                for func in functions:
                    print(f"   - {func.get('name', 'Unknown')}: {func.get('title', 'No title')}")
                return functions
            else:
                print(f"❌ 無法獲取函數列表: HTTP {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ 獲取函數列表時發生錯誤: {e}")
            return []

    def test_rag_integration(self):
        """測試RAG集成功能"""
        print("\n🧪 開始RAG集成測試...")

        test_cases = [
            {
                "model": "qwen3-4b-basic_rag",
                "query": "印象派的特色是什麼？",
                "description": "中文藝術史查詢測試"
            },
            {
                "model": "gpt-oss-20b-agentic_rag",
                "query": "分析達文西的科學研究如何影響他的藝術創作",
                "description": "複雜推理分析測試"
            },
            {
                "model": "gemma3-1b-naive_rag",
                "query": "梵谷",
                "description": "極速響應測試"
            }
        ]

        for i, test in enumerate(test_cases, 1):
            print(f"\n📝 測試 {i}/3: {test['description']}")
            print(f"   模型: {test['model']}")
            print(f"   查詢: {test['query']}")

            # 測試模型是否可用
            if self.test_model_availability(test['model']):
                print(f"   ✅ 模型 {test['model']} 可用")

                # 測試查詢
                if self.test_model_query(test['model'], test['query']):
                    print(f"   ✅ 查詢測試通過")
                else:
                    print(f"   ❌ 查詢測試失敗")
            else:
                print(f"   ❌ 模型 {test['model']} 不可用")

    def test_model_availability(self, model_name):
        """測試模型是否可用"""
        try:
            # 通過Ollama API檢查模型
            response = requests.get("http://localhost:11434/api/tags")
            if response.status_code == 200:
                models = response.json().get('models', [])
                available_models = [m['name'] for m in models]
                return any(model_name in model for model in available_models)
            return False
        except:
            return False

    def test_model_query(self, model_name, query):
        """測試模型查詢"""
        try:
            # 通過Ollama API測試查詢
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": model_name,
                    "prompt": query,
                    "stream": False
                },
                timeout=30
            )
            return response.status_code == 200
        except:
            return False

def main():
    print("🎨 OpenWebUI RAG+LLM組合系統自動上傳工具")
    print("=" * 50)

    # 創建上傳器實例
    uploader = OpenWebUIUploader()

    # 函數文件路徑
    function_file = "/mnt/c/Users/ssking1999/Desktop/藝術史資料庫/art-history-database/enhanced_openwebui_rag_function_v3.py"

    # 檢查文件是否存在
    if not os.path.exists(function_file):
        print(f"❌ 錯誤: 函數文件不存在: {function_file}")
        print("\n💡 請確認文件路徑正確，或手動上傳函數。")
        return

    print(f"📁 函數文件路徑: {function_file}")
    print(f"📦 文件大小: {os.path.getsize(function_file)} bytes")

    # 顯示函數內容摘要
    try:
        with open(function_file, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            print(f"📄 文件行數: {len(lines)}")

            # 提取函數標題
            for line in lines[:20]:
                if 'title:' in line:
                    print(f"🏷️  {line.strip()}")
                    break
    except:
        pass

    print("\n" + "=" * 50)
    print("📋 可選操作:")
    print("1. 嘗試自動上傳函數 (可能需要API認證)")
    print("2. 顯示手動上傳指南")
    print("3. 測試已註冊的模型")
    print("4. 檢查RAG服務狀態")

    choice = input("\n請選擇操作 (1-4): ").strip()

    if choice == "1":
        print("\n🚀 嘗試自動上傳...")
        if uploader.upload_function(function_file):
            print("✅ 自動上傳成功！")
            uploader.list_functions()
        else:
            print("❌ 自動上傳失敗，請嘗試手動上傳。")
            show_manual_guide()

    elif choice == "2":
        show_manual_guide()

    elif choice == "3":
        uploader.test_rag_integration()

    elif choice == "4":
        check_rag_service()

    else:
        print("無效選擇，顯示手動上傳指南...")
        show_manual_guide()

def show_manual_guide():
    """顯示手動上傳指南"""
    print("\n📖 手動上傳指南")
    print("=" * 30)

    print("1. 📂 打開文件管理器，導航到:")
    print("   /mnt/c/Users/ssking1999/Desktop/藝術史資料庫/art-history-database/")

    print("\n2. 📋 複製函數內容:")
    print("   - 用文本編輯器打開 'enhanced_openwebui_rag_function_v3.py'")
    print("   - 全選並複製所有內容 (Ctrl+A, Ctrl+C)")

    print("\n3. 🌐 打開OpenWebUI:")
    print("   - 訪問您的OpenWebUI界面 (通常是 http://localhost:3000)")
    print("   - 點擊右上角的 'Settings' (設置)")
    print("   - 選擇左側菜單的 'Functions' (函數)")

    print("\n4. ➕ 添加函數:")
    print("   - 點擊 '+ Add Function' 或 'Import Function'")
    print("   - 選擇 'Paste Code' 或 'Import from Content'")
    print("   - 貼上複製的函數內容 (Ctrl+V)")
    print("   - 點擊 'Save' 或 'Import'")

    print("\n5. ✅ 啟用函數:")
    print("   - 確保函數狀態為 'Enabled' (已啟用)")
    print("   - 如果是 'Disabled'，點擊切換開關")

    print("\n6. 🧪 測試功能:")
    print("   - 回到聊天界面")
    print("   - 在模型選擇下拉菜單中查找:")
    print("     • qwen3-4b-basic_rag")
    print("     • gpt-oss-20b-agentic_rag")
    print("     • gemma3-1b-naive_rag")

def check_rag_service():
    """檢查RAG服務狀態"""
    print("\n🔍 檢查RAG服務狀態...")

    services = [
        ("RAG管理API", "http://localhost:8008/health"),
        ("Ollama API", "http://localhost:11434/api/tags"),
        ("OpenWebUI", "http://localhost:3000")
    ]

    for name, url in services:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {name}: 運行正常")
            else:
                print(f"❌ {name}: HTTP {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"❌ {name}: 無法連接")
        except requests.exceptions.Timeout:
            print(f"⏱️  {name}: 連接超時")
        except Exception as e:
            print(f"❌ {name}: 錯誤 - {e}")

if __name__ == "__main__":
    main()