#!/usr/bin/env python3
"""
OpenWebUI 連接完整測試腳本
測試 OpenWebUI 到所有資料庫的連接狀態
"""

import sys
import requests
from neo4j import GraphDatabase

print("=" * 70)
print("🔍 OpenWebUI 資料庫連接完整測試")
print("=" * 70)
print()

# 測試結果記錄
results = {
    "chromadb_data": False,
    "neo4j_data": False,
    "ollama_api": False,
    "openwebui_to_chromadb": False,
    "openwebui_to_ollama": False,
    "data_retrieval": False
}

# ==================== 測試 1: ChromaDB 資料完整性 ====================
print("📊 測試 1: ChromaDB 資料完整性")
print("-" * 70)

try:
    import chromadb
    client = chromadb.HttpClient(host='localhost', port=8000)
    collection = client.get_collection('art_history_collection')
    all_data = collection.get()

    doc_count = len(all_data['ids'])
    print(f"✅ ChromaDB 連接成功")
    print(f"   集合: art_history_collection")
    print(f"   文檔數: {doc_count}")

    if doc_count >= 6:
        results["chromadb_data"] = True
        print(f"   ✅ 資料完整 (預期 6 個，實際 {doc_count} 個)")
    else:
        print(f"   ⚠️  資料不完整 (預期 6 個，實際 {doc_count} 個)")

    # 顯示文檔列表
    print(f"\n   文檔列表:")
    for i, (doc_id, meta) in enumerate(zip(all_data['ids'][:6], all_data['metadatas'][:6]), 1):
        title = meta.get('title', 'N/A')
        source = meta.get('source', 'N/A')
        print(f"   {i}. {title[:55]}")
        print(f"      來源: {source}")

except Exception as e:
    print(f"❌ ChromaDB 測試失敗: {e}")

print()

# ==================== 測試 2: Neo4j 資料完整性 ====================
print("📊 測試 2: Neo4j 資料完整性")
print("-" * 70)

try:
    driver = GraphDatabase.driver(
        "bolt://localhost:7687",
        auth=("neo4j", "arthistory123")
    )

    with driver.session() as session:
        # 查詢本地資料
        result = session.run(
            "MATCH (n:Artwork) WHERE n.source CONTAINS 'local' RETURN count(n) as count"
        )
        count = result.single()['count']

        print(f"✅ Neo4j 連接成功")
        print(f"   本地匯入的作品數: {count}")

        if count >= 6:
            results["neo4j_data"] = True
            print(f"   ✅ 資料完整 (至少 6 個節點)")
        else:
            print(f"   ⚠️  資料不完整 (少於 6 個節點)")

        # 顯示部分資料
        result = session.run("""
            MATCH (n:Artwork)
            WHERE n.source CONTAINS 'local'
            RETURN n.title as title
            LIMIT 6
        """)

        print(f"\n   作品列表:")
        for i, record in enumerate(result, 1):
            print(f"   {i}. {record['title'][:60]}")

    driver.close()

except Exception as e:
    print(f"❌ Neo4j 測試失敗: {e}")

print()

# ==================== 測試 3: Ollama API ====================
print("📊 測試 3: Ollama API")
print("-" * 70)

try:
    response = requests.post(
        'http://localhost:11434/api/embeddings',
        json={
            'model': 'nomic-embed-text',
            'prompt': '測試'
        },
        timeout=10
    )

    if response.status_code == 200:
        embedding = response.json()['embedding']
        print(f"✅ Ollama API 正常")
        print(f"   嵌入模型: nomic-embed-text")
        print(f"   向量維度: {len(embedding)}")
        results["ollama_api"] = True
    else:
        print(f"❌ Ollama API 錯誤: {response.status_code}")

except Exception as e:
    print(f"❌ Ollama 測試失敗: {e}")

print()

# ==================== 測試 4: OpenWebUI 到 ChromaDB ====================
print("📊 測試 4: OpenWebUI 到 ChromaDB 連接")
print("-" * 70)

try:
    import subprocess

    # 測試不同的主機名
    test_hosts = [
        ('chromadb', '簡化主機名'),
        ('art-history-chromadb', '完整容器名'),
        ('172.18.0.6', 'IP (art-history-network)'),
        ('172.25.0.8', 'IP (art-database_art-network)')
    ]

    for host, desc in test_hosts:
        cmd = f"""docker exec art-history-openwebui python3 -c "
import chromadb
try:
    client = chromadb.HttpClient(host='{host}', port=8000)
    collections = client.list_collections()
    print('{host}')
    print('{len(collections) if 'collections' in locals() else 0}')
except Exception as e:
    print('ERROR')
    print(str(e))
" 2>&1"""

        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        output_lines = result.stdout.strip().split('\n')

        if len(output_lines) >= 2 and output_lines[0] == host:
            try:
                coll_count = int(output_lines[1])
                print(f"   ✅ {desc} ({host}): 成功 - {coll_count} collections")
                if host == 'chromadb':
                    results["openwebui_to_chromadb"] = True
            except:
                pass
        else:
            print(f"   ❌ {desc} ({host}): 失敗")

    if not results["openwebui_to_chromadb"]:
        print(f"\n   ⚠️  OpenWebUI 無法使用 'chromadb' 連接")
        print(f"   💡 需要修改環境變數為 'art-history-chromadb'")

except Exception as e:
    print(f"❌ 測試失敗: {e}")

print()

# ==================== 測試 5: OpenWebUI 到 Ollama ====================
print("📊 測試 5: OpenWebUI 到 Ollama 連接")
print("-" * 70)

try:
    import subprocess

    cmd = """docker exec art-history-openwebui python3 -c "
import requests
try:
    # 從環境變數獲取 OLLAMA_BASE_URL
    import os
    ollama_url = os.getenv('OLLAMA_BASE_URL', 'http://ollama:11434')

    response = requests.get(f'{ollama_url}/api/tags', timeout=5)
    if response.status_code == 200:
        print('SUCCESS')
    else:
        print('ERROR')
        print(response.status_code)
except Exception as e:
    print('ERROR')
    print(str(e))
" 2>&1"""

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if 'SUCCESS' in result.stdout:
        print(f"   ✅ OpenWebUI → Ollama: 連接成功")
        results["openwebui_to_ollama"] = True
    else:
        print(f"   ❌ OpenWebUI → Ollama: 連接失敗")
        print(f"   輸出: {result.stdout}")

except Exception as e:
    print(f"❌ 測試失敗: {e}")

print()

# ==================== 測試 6: 端到端檢索測試 ====================
print("📊 測試 6: 端到端資料檢索")
print("-" * 70)

try:
    import chromadb
    import requests

    # 使用 Ollama 生成查詢向量
    response = requests.post(
        'http://localhost:11434/api/embeddings',
        json={
            'model': 'nomic-embed-text',
            'prompt': '漢寶德是誰'
        }
    )

    if response.status_code == 200:
        query_embedding = response.json()['embedding']

        # 從 ChromaDB 檢索
        client = chromadb.HttpClient(host='localhost', port=8000)
        collection = client.get_collection('art_history_collection')

        results_data = collection.query(
            query_embeddings=[query_embedding],
            n_results=3
        )

        print(f"✅ 檢索測試成功")
        print(f"   查詢: 「漢寶德是誰」")
        print(f"   找到 {len(results_data['documents'][0])} 個相關結果")

        for i, (doc, meta, distance) in enumerate(zip(
            results_data['documents'][0],
            results_data['metadatas'][0],
            results_data['distances'][0]
        ), 1):
            title = meta.get('title', 'N/A')
            similarity = 1 - distance
            print(f"   {i}. {title[:50]} (相似度: {similarity:.3f})")

        results["data_retrieval"] = True

except Exception as e:
    print(f"❌ 檢索測試失敗: {e}")

print()

# ==================== 總結 ====================
print("=" * 70)
print("📋 測試總結")
print("=" * 70)

total_tests = len(results)
passed_tests = sum(results.values())

print(f"\n通過測試: {passed_tests}/{total_tests}")
print()

status_icon = lambda x: "✅" if x else "❌"

print(f"{status_icon(results['chromadb_data'])} ChromaDB 資料完整性")
print(f"{status_icon(results['neo4j_data'])} Neo4j 資料完整性")
print(f"{status_icon(results['ollama_api'])} Ollama API")
print(f"{status_icon(results['openwebui_to_chromadb'])} OpenWebUI → ChromaDB 連接")
print(f"{status_icon(results['openwebui_to_ollama'])} OpenWebUI → Ollama 連接")
print(f"{status_icon(results['data_retrieval'])} 端到端資料檢索")

print()
print("=" * 70)

# 提供建議
if not results['openwebui_to_chromadb']:
    print("⚠️  關鍵問題: OpenWebUI 無法連接到 ChromaDB")
    print()
    print("解決方案:")
    print("1. 修改 OpenWebUI 環境變數:")
    print("   CHROMA_HTTP_HOST=art-history-chromadb")
    print()
    print("2. 或在 OpenWebUI 中手動上傳文檔:")
    print("   訪問 http://localhost:8080 > Workspace > Documents")
    print()
    print("詳細說明請參考: OpenWebUI資料庫連接診斷與修復.md")
    print("=" * 70)
    sys.exit(1)
elif passed_tests == total_tests:
    print("🎉 所有測試通過！系統連接正常。")
    print("=" * 70)
    sys.exit(0)
else:
    print("⚠️  部分測試失敗，請檢查上述錯誤訊息。")
    print("=" * 70)
    sys.exit(1)
