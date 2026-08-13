#!/usr/bin/env python3
"""
直接將 Function 插入到 OpenWebUI 資料庫
這個腳本會在 Docker 容器內執行
"""

import sqlite3
import json
import hashlib
from datetime import datetime
import os

def insert_function_to_db():
    """直接插入 Function 到資料庫"""

    # 讀取 Function 文件
    function_file = "/tmp/enhanced_openwebui_rag_function_v4.py"

    if not os.path.exists(function_file):
        print(f"❌ Function 文件不存在: {function_file}")
        return False

    with open(function_file, 'r', encoding='utf-8') as f:
        function_content = f.read()

    print(f"✅ 已讀取 Function 文件 ({len(function_content)} 字符)")

    # 連接資料庫
    db_path = "/app/backend/data/webui.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 查看所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"\n📊 資料庫中的表: {', '.join(tables)}")

    # 查找 function 相關的表
    function_table = None
    for table in tables:
        if 'function' in table.lower():
            function_table = table
            break

    if not function_table:
        print("\n❌ 未找到 function 表")
        print("可能的表名:")
        for table in tables:
            print(f"  - {table}")
        conn.close()
        return False

    print(f"\n✅ 找到 Function 表: {function_table}")

    # 查看表結構
    cursor.execute(f"PRAGMA table_info({function_table})")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    print(f"📋 表結構: {', '.join(column_names)}")

    # 檢查是否已有相同的 Function
    cursor.execute(f"SELECT id, name FROM {function_table}")
    existing_functions = cursor.fetchall()
    print(f"\n📚 現有 Functions ({len(existing_functions)} 個):")
    for func in existing_functions:
        print(f"  - ID: {func[0]}, Name: {func[1]}")

    # 生成 Function ID
    function_id = hashlib.md5(b"enhanced_openwebui_rag_function_v4").hexdigest()[:16]

    # 準備插入數據
    now = datetime.now().isoformat()

    # 構建插入語句（根據實際表結構）
    # 這是一個通用的嘗試，可能需要根據實際結構調整
    try:
        # 嘗試方法 1: 完整欄位
        insert_sql = f"""
        INSERT OR REPLACE INTO {function_table}
        (id, user_id, name, type, content, meta, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """

        meta = json.dumps({
            "title": "藝術史 RAG+LLM 完整智能組合系統 v4.1 - 多資料庫整合",
            "version": "4.1.0",
            "description": "支援5種LLM模型 × 8種RAG策略，整合Neo4j+ChromaDB雙資料庫"
        })

        cursor.execute(insert_sql, (
            function_id,
            "default",  # user_id
            "enhanced_openwebui_rag_function_v4",
            "function",
            function_content,
            meta,
            now,
            now
        ))

        conn.commit()
        print(f"\n✅ Function 已成功插入！")
        print(f"   ID: {function_id}")
        print(f"   Name: enhanced_openwebui_rag_function_v4")

        conn.close()
        return True

    except sqlite3.Error as e:
        print(f"\n❌ 插入失敗: {e}")
        print("\n嘗試其他方法...")

        # 嘗試方法 2: 簡化欄位
        try:
            insert_sql = f"""
            INSERT OR REPLACE INTO {function_table}
            (id, name, content, created_at)
            VALUES (?, ?, ?, ?)
            """

            cursor.execute(insert_sql, (
                function_id,
                "enhanced_openwebui_rag_function_v4",
                function_content,
                now
            ))

            conn.commit()
            print(f"✅ Function 已成功插入（簡化版）！")
            conn.close()
            return True

        except sqlite3.Error as e2:
            print(f"❌ 再次失敗: {e2}")
            conn.close()
            return False

if __name__ == "__main__":
    print("🎨 OpenWebUI Function 直接資料庫插入工具")
    print("="*60)

    result = insert_function_to_db()

    if result:
        print("\n" + "="*60)
        print("🎉 成功！")
        print("="*60)
        print("\n請重啟 OpenWebUI 容器以載入新 Function:")
        print("  docker restart art-history-openwebui")
    else:
        print("\n" + "="*60)
        print("❌ 失敗")
        print("="*60)
        print("\n需要手動通過網頁界面添加 Function")
