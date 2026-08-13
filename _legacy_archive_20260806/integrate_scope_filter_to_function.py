#!/usr/bin/env python3
"""
自動整合問題範圍過濾器到 OpenWebUI Function
讀取現有 Function，整合過濾器，生成新版本
"""

import re

def integrate_filter():
    """整合範圍過濾器到 Function"""

    print("🔧 開始整合問題範圍過濾器到 OpenWebUI Function...")
    print("="*60)

    # 1. 讀取過濾器代碼
    print("\n📖 步驟 1: 讀取過濾器模組...")
    try:
        with open("art_history_scope_filter.py", "r", encoding="utf-8") as f:
            filter_code = f.read()

        # 提取 ArtHistoryScopeFilter 類定義
        class_match = re.search(
            r'class ArtHistoryScopeFilter:.*?(?=\n\n# 測試函數|if __name__|$)',
            filter_code,
            re.DOTALL
        )

        if not class_match:
            raise ValueError("無法提取 ArtHistoryScopeFilter 類定義")

        filter_class = class_match.group(0).strip()
        print("   ✅ 過濾器類定義已提取")

    except Exception as e:
        print(f"   ❌ 錯誤: {e}")
        return False

    # 2. 讀取現有 Function
    print("\n📖 步驟 2: 讀取現有 OpenWebUI Function...")
    try:
        with open("enhanced_openwebui_rag_function_v4.py", "r", encoding="utf-8") as f:
            function_code = f.read()
        print("   ✅ Function 代碼已讀取")

    except Exception as e:
        print(f"   ❌ 錯誤: {e}")
        return False

    # 3. 更新版本信息
    print("\n🔄 步驟 3: 更新版本信息...")
    function_code = re.sub(
        r'version: \d+\.\d+\.\d+',
        'version: 5.0.0',
        function_code
    )
    function_code = re.sub(
        r'title: (.+)',
        r'title: \1 (含問題範圍限制)',
        function_code
    )
    print("   ✅ 版本更新為 v5.0.0")

    # 4. 插入過濾器類
    print("\n📝 步驟 4: 插入過濾器類定義...")

    # 找到 Tools 類定義的位置
    tools_class_pos = function_code.find('class Tools:')

    if tools_class_pos == -1:
        print("   ❌ 錯誤: 找不到 Tools 類定義")
        return False

    # 在 Tools 類之前插入過濾器類
    filter_section = f'''
# ===== 藝術史問題範圍過濾器 =====
# 自動判斷問題是否屬於藝術史領域
# 拒絕非藝術史相關的問題，提供友好的範圍說明

{filter_class}

# ===== OpenWebUI Function 主類 =====

'''

    function_code = (
        function_code[:tools_class_pos] +
        filter_section +
        function_code[tools_class_pos:]
    )
    print("   ✅ 過濾器類已插入")

    # 5. 修改 pipe() 函數，添加範圍檢查
    print("\n🔄 步驟 5: 在 pipe() 函數中添加範圍檢查...")

    # 找到 pipe 函數定義
    pipe_def_pattern = r'(async def pipe\(self, body: dict\).*?:.*?\n)(.*?)(\n        # .*?檢索策略)'

    def add_filter_check(match):
        pipe_signature = match.group(1)
        original_content = match.group(2)
        next_section = match.group(3)

        filter_logic = '''
        # ===== 問題範圍檢查 =====
        # 提取使用者問題
        messages = body.get("messages", [])
        if not messages:
            return "無法獲取使用者問題"

        user_message = messages[-1].get("content", "")

        # 使用過濾器檢查問題範圍
        scope_filter = ArtHistoryScopeFilter()
        filter_result = scope_filter.is_art_history_related(user_message)

        # 如果問題不在藝術史範圍內，返回友好拒絕訊息
        if not filter_result["is_related"]:
            rejection_message = scope_filter.get_rejection_message(
                user_message,
                filter_result
            )
            return rejection_message

        # 問題通過範圍檢查，繼續正常流程
        # ===== 範圍檢查通過，開始 RAG 檢索 =====
'''

        return pipe_signature + filter_logic + next_section

    function_code = re.sub(
        pipe_def_pattern,
        add_filter_check,
        function_code,
        count=1,
        flags=re.DOTALL
    )
    print("   ✅ 範圍檢查邏輯已添加到 pipe() 函數")

    # 6. 保存新版本 Function
    print("\n💾 步驟 6: 保存新版本 Function...")
    output_file = "enhanced_openwebui_rag_function_v5_with_filter.py"

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(function_code)
        print(f"   ✅ 新版本已保存到: {output_file}")

    except Exception as e:
        print(f"   ❌ 錯誤: {e}")
        return False

    # 7. 生成摘要
    print("\n" + "="*60)
    print("🎉 整合完成！")
    print("="*60)
    print("\n📊 整合摘要:")
    print(f"  • 輸入文件: enhanced_openwebui_rag_function_v4.py")
    print(f"  • 輸出文件: {output_file}")
    print(f"  • 新版本: v5.0.0 (含問題範圍限制)")
    print(f"  • 新增功能: 自動過濾非藝術史問題")

    print("\n📝 下一步操作:")
    print("  1. 打開 OpenWebUI: http://localhost:8080")
    print("  2. 進入 Workspace → Functions")
    print("  3. 找到 '藝術史 RAG+LLM 完整智能組合系統'")
    print("  4. 點擊編輯，複製新文件內容並保存")
    print(f"  5. 詳細步驟請參考: 藝術史範圍限制設置指南.md")

    print("\n✅ 測試建議:")
    print("  測試問題 1: '莫內的睡蓮系列有什麼特色？' (應該通過)")
    print("  測試問題 2: 'Python 怎麼連接資料庫？' (應該拒絕)")

    return True


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🎨 藝術史 OpenWebUI Function 範圍過濾器整合工具")
    print("="*60)

    success = integrate_filter()

    if success:
        print("\n✅ 整合成功！")
        exit(0)
    else:
        print("\n❌ 整合失敗，請檢查錯誤訊息。")
        exit(1)
