#!/usr/bin/env python3
"""
同步 ChromaDB 資料到 OpenWebUI
將 ChromaDB 中的文檔註冊到 OpenWebUI 的 document 表中
"""

import chromadb
import sqlite3
import hashlib
from datetime import datetime

def sync_chromadb_to_openwebui(
    chromadb_host='localhost',
    chromadb_port=8000,
    collection_name='art_history_collection',
    openwebui_db_path='/app/backend/data/webui.db',
    user_id='1b9db215-ff41-4267-b44a-c579cfafcba9',  # 從 knowledge 表取得
    knowledge_id='e4590fbc-7c59-4915-b730-0cc8a16296df'  # 從 knowledge 表取得
):
    """
    將 ChromaDB 中的文檔同步到 OpenWebUI

    Args:
        chromadb_host: ChromaDB 主機
        chromadb_port: ChromaDB 端口
        collection_name: Collection 名稱
        openwebui_db_path: OpenWebUI 資料庫路徑
        user_id: OpenWebUI 使用者 ID
        knowledge_id: Knowledge Base ID
    """

    print("="*60)
    print("同步 ChromaDB 到 OpenWebUI")
    print("="*60)
    print()

    # 1. 連接 ChromaDB
    print(f"1️⃣ 連接 ChromaDB ({chromadb_host}:{chromadb_port})...")
    try:
        client = chromadb.HttpClient(host=chromadb_host, port=chromadb_port)
        collection = client.get_collection(collection_name)
        total_docs = collection.count()
        print(f"   ✅ Collection '{collection_name}' 有 {total_docs} 個文檔")
    except Exception as e:
        print(f"   ❌ 連接失敗: {e}")
        return False

    print()

    # 2. 取得所有文檔
    print("2️⃣ 從 ChromaDB 取得所有文檔...")
    try:
        results = collection.get(
            limit=total_docs,
            include=['documents', 'metadatas']
        )
        docs = results['documents']
        metadatas = results['metadatas']
        ids = results['ids']
        print(f"   ✅ 取得 {len(docs)} 個文檔")
    except Exception as e:
        print(f"   ❌ 取得失敗: {e}")
        return False

    print()

    # 3. 連接 OpenWebUI 資料庫
    print("3️⃣ 連接 OpenWebUI 資料庫...")
    try:
        conn = sqlite3.connect(openwebui_db_path)
        cursor = conn.cursor()
        print(f"   ✅ 連接成功")
    except Exception as e:
        print(f"   ❌ 連接失敗: {e}")
        return False

    print()

    # 4. 檢查現有文檔
    print("4️⃣ 檢查現有文檔...")
    cursor.execute("SELECT COUNT(*) FROM document WHERE collection_name = ?", (collection_name,))
    existing_count = cursor.fetchone()[0]
    print(f"   現有文檔: {existing_count}")

    if existing_count > 0:
        print(f"   ⚠️  已有 {existing_count} 個文檔，將清空並重新匯入")
        cursor.execute("DELETE FROM document WHERE collection_name = ?", (collection_name,))
        conn.commit()
        print("   ✅ 清空完成")

    print()

    # 5. 插入文檔到 document 表
    print("5️⃣ 插入文檔到 OpenWebUI...")

    timestamp = int(datetime.now().timestamp())
    inserted_count = 0

    for i, (doc_id, doc, meta) in enumerate(zip(ids, docs, metadatas), 1):
        try:
            # 準備資料
            title = meta.get('title', '未命名文檔')
            filename = f"{title}.txt"  # OpenWebUI 需要檔案名
            name = doc_id  # 使用 ChromaDB 的 ID 作為 name

            # 插入到 document 表
            cursor.execute("""
                INSERT INTO document (
                    collection_name,
                    name,
                    title,
                    filename,
                    content,
                    user_id,
                    timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                collection_name,
                name,
                title,
                filename,
                doc[:1000],  # 只存儲前 1000 字符作為預覽
                user_id,
                timestamp
            ))

            inserted_count += 1

            if i % 5 == 0 or i == len(docs):
                print(f"   進度: {i}/{len(docs)}")

        except Exception as e:
            print(f"   ⚠️  文檔 {i} 插入失敗: {e}")

    # 提交變更
    conn.commit()
    conn.close()

    print(f"   ✅ 成功插入 {inserted_count} 個文檔")
    print()

    print("="*60)
    print("✅ 同步完成！")
    print("="*60)
    print()
    print(f"📊 統計:")
    print(f"   ChromaDB 文檔: {total_docs}")
    print(f"   OpenWebUI 文檔: {inserted_count}")
    print()
    print("💡 後續步驟:")
    print("   1. 重新啟動 OpenWebUI 容器 (可選)")
    print("   2. 在 OpenWebUI 中測試問題")
    print("   3. 確認 Knowledge Base 可以檢索到資料")
    print()

    return True


def get_openwebui_info():
    """
    取得 OpenWebUI 的 user_id 和 knowledge_id
    """
    print("🔍 取得 OpenWebUI 資訊...")
    print()

    # 這個需要在容器內執行
    import os
    db_path = os.getenv('OPENWEBUI_DB_PATH', '/app/backend/data/webui.db')

    if not os.path.exists(db_path):
        print(f"❌ 資料庫不存在: {db_path}")
        print("   請在 OpenWebUI 容器內執行此腳本")
        return None, None

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 取得第一個使用者
    cursor.execute("SELECT id FROM user LIMIT 1")
    user = cursor.fetchone()
    user_id = user[0] if user else None

    # 取得 Knowledge Base
    cursor.execute("SELECT id, name FROM knowledge LIMIT 1")
    knowledge = cursor.fetchone()
    knowledge_id = knowledge[0] if knowledge else None
    knowledge_name = knowledge[1] if knowledge else None

    conn.close()

    if user_id and knowledge_id:
        print(f"✅ User ID: {user_id}")
        print(f"✅ Knowledge ID: {knowledge_id}")
        print(f"✅ Knowledge Name: {knowledge_name}")
        return user_id, knowledge_id
    else:
        print("❌ 無法取得必要資訊")
        return None, None


if __name__ == "__main__":
    import argparse
    import sys
    import os

    parser = argparse.ArgumentParser(description='同步 ChromaDB 到 OpenWebUI')
    parser.add_argument('--chromadb-host', default='localhost', help='ChromaDB 主機')
    parser.add_argument('--chromadb-port', type=int, default=8000, help='ChromaDB 端口')
    parser.add_argument('--collection', default='art_history_collection', help='Collection 名稱')
    parser.add_argument('--inside-container', action='store_true', help='在 OpenWebUI 容器內執行')

    args = parser.parse_args()

    if args.inside_container:
        # 在容器內執行，自動取得資訊
        user_id, knowledge_id = get_openwebui_info()

        if not user_id or not knowledge_id:
            print()
            print("❌ 無法取得必要資訊，請手動指定:")
            print("   python3 sync_chromadb_to_openwebui.py --user-id <USER_ID> --knowledge-id <KNOWLEDGE_ID>")
            sys.exit(1)

        db_path = '/app/backend/data/webui.db'
    else:
        # 從外部執行，使用預設值
        print("⚠️  從外部執行，使用預設 user_id 和 knowledge_id")
        print("   如果失敗，請使用 --inside-container 在容器內執行")
        print()
        user_id = '1b9db215-ff41-4267-b44a-c579cfafcba9'
        knowledge_id = 'e4590fbc-7c59-4915-b730-0cc8a16296df'
        db_path = '/app/backend/data/webui.db'

    # 執行同步
    success = sync_chromadb_to_openwebui(
        chromadb_host=args.chromadb_host,
        chromadb_port=args.chromadb_port,
        collection_name=args.collection,
        openwebui_db_path=db_path,
        user_id=user_id,
        knowledge_id=knowledge_id
    )

    sys.exit(0 if success else 1)
