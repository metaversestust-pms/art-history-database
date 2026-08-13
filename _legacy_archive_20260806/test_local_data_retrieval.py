#!/usr/bin/env python3
"""
測試本地匯入資料的檢索功能
確認 ChromaDB 和 Neo4j 中的資料是否可以正確檢索
"""

import chromadb
import requests
from neo4j import GraphDatabase

print("=" * 60)
print("🔍 本地資料檢索測試")
print("=" * 60)

# ==================== 測試 ChromaDB ====================
print("\n📊 測試 1: ChromaDB 資料檢查")
print("-" * 60)

try:
    client = chromadb.HttpClient(host='localhost', port=8000)
    collection = client.get_collection('art_history_collection')

    # 獲取所有資料
    all_data = collection.get()
    print(f"✅ ChromaDB 連接成功")
    print(f"   集合名稱: art_history_collection")
    print(f"   文檔總數: {len(all_data['ids'])}")

    # 顯示前3個文檔的metadata
    print(f"\n   文檔列表:")
    for i, (doc_id, metadata) in enumerate(zip(all_data['ids'][:6], all_data['metadatas'][:6]), 1):
        title = metadata.get('title', 'N/A')
        source = metadata.get('source', 'N/A')
        print(f"   {i}. {title[:50]}")
        print(f"      來源: {source}")

except Exception as e:
    print(f"❌ ChromaDB 錯誤: {e}")

# ==================== 測試使用 Ollama 向量檢索 ====================
print("\n📊 測試 2: 使用 Ollama 嵌入模型檢索")
print("-" * 60)

def get_ollama_embedding(text):
    """使用 Ollama 的 nomic-embed-text 模型生成嵌入向量"""
    response = requests.post(
        'http://localhost:11434/api/embeddings',
        json={
            'model': 'nomic-embed-text',
            'prompt': text
        }
    )
    if response.status_code == 200:
        return response.json()['embedding']
    else:
        raise Exception(f"Ollama API 錯誤: {response.status_code}")

# 測試查詢
test_queries = [
    "漢寶德是誰",
    "南藝大",
    "漢寶德紀念館"
]

for query in test_queries:
    print(f"\n🔍 查詢: 「{query}」")
    try:
        # 生成查詢向量
        query_embedding = get_ollama_embedding(query)
        print(f"   ✅ 生成嵌入向量 (維度: {len(query_embedding)})")

        # 檢索
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=3
        )

        print(f"   ✅ 找到 {len(results['documents'][0])} 個相關結果:")
        for i, (doc, meta, distance) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        ), 1):
            title = meta.get('title', 'N/A')
            print(f"      {i}. {title} (相似度: {1-distance:.3f})")
            print(f"         內容預覽: {doc[:100]}...")

    except Exception as e:
        print(f"   ❌ 錯誤: {e}")

# ==================== 測試 Neo4j ====================
print("\n\n📊 測試 3: Neo4j 資料檢查")
print("-" * 60)

try:
    driver = GraphDatabase.driver(
        "bolt://localhost:7687",
        auth=("neo4j", "arthistory123")
    )

    with driver.session() as session:
        # 查詢本地匯入的資料數量
        result = session.run(
            "MATCH (n:Artwork) WHERE n.source CONTAINS 'local' RETURN count(n) as count"
        )
        count = result.single()['count']
        print(f"✅ Neo4j 連接成功")
        print(f"   本地匯入的作品數: {count}")

        # 查詢具體的資料
        result = session.run("""
            MATCH (n:Artwork)
            WHERE n.source CONTAINS 'local'
            RETURN n.title as title, n.file_path as file_path
            LIMIT 6
        """)

        print(f"\n   作品列表:")
        for i, record in enumerate(result, 1):
            print(f"   {i}. {record['title'][:60]}")
            print(f"      檔案: {record['file_path']}")

    driver.close()

except Exception as e:
    print(f"❌ Neo4j 錯誤: {e}")

# ==================== 測試結論 ====================
print("\n" + "=" * 60)
print("📋 測試總結")
print("=" * 60)
print("""
如果以上測試都成功:
✅ 資料已正確存入資料庫
✅ 使用 Ollama 嵌入模型可以正確檢索

如果 OpenWebUI 仍然回答錯誤,可能的原因:
1. RAG 服務器 (port 8002) 未運行
2. OpenWebUI 沒有配置使用正確的 RAG 功能
3. 需要重啟 OpenWebUI 容器讓配置生效

解決方案:
• 方案 1: 啟動 RAG 服務器 (enhanced_rag_strategy_server.py)
• 方案 2: 在 OpenWebUI 中直接使用 Ollama 模型 + Knowledge Base
• 方案 3: 配置 OpenWebUI 的 RAG 設定指向正確的資料庫
""")
print("=" * 60)
