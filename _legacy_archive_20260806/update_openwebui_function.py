#!/usr/bin/env python3
"""
OpenWebUI Function 自動更新工具 v4.1
自動上傳/更新 enhanced_openwebui_rag_function_v4.py 到 OpenWebUI
"""

import requests
import json
import os
import sys

class OpenWebUIUpdater:
    def __init__(self, openwebui_url="http://localhost:8080"):
        self.base_url = openwebui_url
        self.session = requests.Session()

    def update_function(self, function_file_path):
        """更新 Function 到 OpenWebUI"""
        print(f"🚀 開始更新 Function: {function_file_path}")
        print(f"🌐 OpenWebUI 地址: {self.base_url}")

        if not os.path.exists(function_file_path):
            print(f"❌ 錯誤: Function 文件不存在: {function_file_path}")
            return False

        try:
            # 讀取函數文件內容
            with open(function_file_path, 'r', encoding='utf-8') as f:
                function_content = f.read()

            print(f"✅ 已讀取 Function 文件 ({len(function_content)} 字符)")

            # 提取 title 和 version
            title = "Unknown"
            version = "Unknown"
            for line in function_content.split('\n')[:10]:
                if 'title:' in line:
                    title = line.split('title:')[1].strip()
                if 'version:' in line:
                    version = line.split('version:')[1].strip()

            print(f"📝 Function 標題: {title}")
            print(f"🏷️  版本: {version}")

            # 嘗試多個可能的 API 端點
            api_endpoints = [
                "/api/v1/functions",
                "/api/functions",
                "/api/v1/functions/import",
                "/functions/import"
            ]

            for endpoint in api_endpoints:
                url = f"{self.base_url}{endpoint}"
                print(f"\n📤 嘗試端點: {url}")

                try:
                    # 嘗試 POST 請求上傳
                    response = self.session.post(
                        url,
                        json={
                            "content": function_content,
                            "name": "enhanced_openwebui_rag_function_v4",
                            "type": "function"
                        },
                        headers={"Content-Type": "application/json"},
                        timeout=10
                    )

                    print(f"   HTTP 狀態: {response.status_code}")

                    if response.status_code == 200:
                        print(f"   ✅ 成功！")
                        return True
                    elif response.status_code == 201:
                        print(f"   ✅ 創建成功！")
                        return True
                    else:
                        print(f"   ❌ 失敗: {response.text[:200]}")

                except requests.exceptions.ConnectionError:
                    print(f"   ❌ 無法連接")
                except requests.exceptions.Timeout:
                    print(f"   ⏱️  超時")
                except Exception as e:
                    print(f"   ❌ 錯誤: {str(e)[:100]}")

            print(f"\n❌ 所有 API 端點都失敗了")
            return False

        except Exception as e:
            print(f"❌ 更新過程中發生錯誤: {e}")
            return False

    def check_openwebui(self):
        """檢查 OpenWebUI 是否運行"""
        print(f"🔍 檢查 OpenWebUI 狀態...")

        try:
            response = requests.get(self.base_url, timeout=5)
            if response.status_code == 200:
                print(f"✅ OpenWebUI 運行正常 ({self.base_url})")
                return True
            else:
                print(f"⚠️  OpenWebUI 返回異常狀態: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print(f"❌ 無法連接到 OpenWebUI ({self.base_url})")
            print(f"   請確認 OpenWebUI 正在運行")
            return False
        except Exception as e:
            print(f"❌ 檢查失敗: {e}")
            return False

def show_manual_instructions():
    """顯示手動更新說明"""
    print("\n" + "="*60)
    print("📖 手動更新說明")
    print("="*60)

    print("\n由於 API 自動更新失敗，請按照以下步驟手動更新：")

    print("\n【步驟 1】複製新代碼")
    print("  1. 打開文件: enhanced_openwebui_rag_function_v4.py")
    print("  2. 全選 (Ctrl + A)")
    print("  3. 複製 (Ctrl + C)")

    print("\n【步驟 2】打開 OpenWebUI")
    print("  1. 瀏覽器訪問: http://localhost:8080")
    print("  2. 登入您的帳號")

    print("\n【步驟 3】進入 Functions 管理")
    print("  嘗試以下路徑之一:")
    print("  方法 A: 左側菜單 → Workspace → Functions")
    print("  方法 B: 左側菜單 → Settings → Admin Settings → Functions")
    print("  方法 C: 直接訪問 http://localhost:8080/workspace/functions")

    print("\n【步驟 4】編輯 Function")
    print("  1. 找到 '藝術史 RAG+LLM 完整智能組合系統 v4.0'")
    print("  2. 點擊 '編輯' 按鈕")
    print("  3. 在代碼編輯器中，全選舊代碼 (Ctrl + A)")
    print("  4. 貼上新代碼 (Ctrl + V)")
    print("  5. 點擊 '保存'")

    print("\n【驗證更新】")
    print("  更新後標題應該顯示:")
    print("  '藝術史 RAG+LLM 完整智能組合系統 v4.1 - 多資料庫整合'")

    print("\n" + "="*60)
    print("📚 詳細指南請查看:")
    print("  - 超簡單更新步驟.md")
    print("  - 找到Function的詳細步驟.md")
    print("="*60 + "\n")

def main():
    print("🎨 OpenWebUI Function 自動更新工具 v4.1")
    print("="*60)

    # Function 文件路徑
    function_file = "/mnt/c/Users/ssking1999/Desktop/藝術史資料庫/art-history-database/enhanced_openwebui_rag_function_v4.py"

    # 檢查文件是否存在
    if not os.path.exists(function_file):
        print(f"❌ 錯誤: Function 文件不存在: {function_file}")
        return

    print(f"📁 Function 文件: enhanced_openwebui_rag_function_v4.py")
    print(f"📦 文件大小: {os.path.getsize(function_file)} bytes")

    # 創建更新器
    updater = OpenWebUIUpdater("http://localhost:8080")

    # 檢查 OpenWebUI
    if not updater.check_openwebui():
        print("\n⚠️  無法連接到 OpenWebUI，請確認:")
        print("   1. OpenWebUI Docker 容器正在運行")
        print("   2. 端口 8080 未被佔用")
        print("   3. 您的瀏覽器能訪問 http://localhost:8080")
        show_manual_instructions()
        return

    print("\n" + "="*60)
    print("🚀 嘗試自動更新 Function...")
    print("="*60 + "\n")

    # 嘗試自動更新
    success = updater.update_function(function_file)

    if success:
        print("\n" + "="*60)
        print("🎉 自動更新成功！")
        print("="*60)
        print("\n請刷新 OpenWebUI 頁面 (F5) 以查看更新")
    else:
        print("\n" + "="*60)
        print("⚠️  自動更新失敗")
        print("="*60)
        print("\nOpenWebUI 的 API 可能需要認證令牌。")
        print("別擔心！手動更新很簡單，只需 3 分鐘。")
        show_manual_instructions()

if __name__ == "__main__":
    main()
