#!/usr/bin/env python3
"""
測試 OpenWebUI 與 Neo4j、ChromaDB 的整合
"""

import requests
import json
import time

def test_neo4j_connection():
    """測試 Neo4j 連接"""
    print("\n" + "="*60)
    print("🔍 測試 Neo4j 連接...")
    print("="*60)

    try:
        response = requests.post(
            "http://localhost:7474/db/neo4j/tx/commit",
            auth=("neo4j", "arthistory123"),
            json={
                "statements": [{
                    "statement": """
                    MATCH (a:Artwork)
                    WHERE a.title IS NOT NULL
                    RETURN a.title as title, labels(a) as labels
                    LIMIT 5
                    """
                }]
            },
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            print("✅ Neo4j 連接成功!")

            if result.get("results") and result["results"][0].get("data"):
                print("\n📊 範例藝術品:")
                for i, item in enumerate(result["results"][0]["data"], 1):
                    title = item["row"][0]
                    labels = item["row"][1]
                    print(f"  {i}. {title} [{', '.join(labels)}]")

            # 統計資料
            stat_response = requests.post(
                "http://localhost:7474/db/neo4j/tx/commit",
                auth=("neo4j", "arthistory123"),
                json={
                    "statements": [{
                        "statement": """
                        MATCH (n)
                        RETURN labels(n)[0] as label, count(n) as count
                        ORDER BY count DESC
                        """
                    }]
                },
                timeout=10
            )

            if stat_response.status_code == 200:
                stat_result = stat_response.json()
                print("\n📈 資料統計:")
                for item in stat_result["results"][0]["data"][:10]:
                    label = item["row"][0]
                    count = item["row"][1]
                    print(f"  • {label}: {count:,} 個節點")

            return True
        else:
            print(f"❌ Neo4j 連接失敗: HTTP {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Neo4j 連接錯誤: {str(e)}")
        return False


def test_chromadb_connection():
    """測試 ChromaDB 連接"""
    print("\n" + "="*60)
    print("🔍 測試 ChromaDB 連接...")
    print("="*60)

    try:
        # 測試心跳
        response = requests.get("http://localhost:8000/api/v2", timeout=5)
        if response.status_code == 200:
            print("✅ ChromaDB 連接成功!")
            print(f"   API 版本: v2")

            # 嘗試列出集合（如果有的話）
            # 注意: ChromaDB v2 API 可能需要不同的端點
            try:
                # 這裡需要根據實際的 ChromaDB API 調整
                print("\n💡 提示: ChromaDB v2 API 已就緒")
                print("   如需查詢集合，請使用適當的 ChromaDB 客戶端")
            except Exception as e:
                pass

            return True
        else:
            print(f"❌ ChromaDB 連接失敗: HTTP {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ ChromaDB 連接錯誤: {str(e)}")
        return False


def test_rag_query(query_text="達文西的蒙娜麗莎"):
    """測試 RAG 查詢功能"""
    print("\n" + "="*60)
    print(f"🔍 測試 RAG 查詢: {query_text}")
    print("="*60)

    # 測試 Neo4j 圖查詢
    print("\n1️⃣ 測試 Neo4j 圖查詢...")
    try:
        response = requests.post(
            "http://localhost:7474/db/neo4j/tx/commit",
            auth=("neo4j", "arthistory123"),
            json={
                "statements": [{
                    "statement": """
                    MATCH (a:Artwork)
                    WHERE a.title CONTAINS $keyword
                       OR a.description CONTAINS $keyword
                    OPTIONAL MATCH (a)-[r]-(related)
                    RETURN a.title as title,
                           a.description as description,
                           type(r) as relationship,
                           labels(related)[0] as related_type,
                           coalesce(related.name, related.title) as related_name
                    LIMIT 3
                    """,
                    "parameters": {"keyword": "蒙娜麗莎"}
                }]
            },
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            if result.get("results") and result["results"][0].get("data"):
                print("   ✅ 找到相關藝術品!")
                for i, item in enumerate(result["results"][0]["data"], 1):
                    row = item["row"]
                    print(f"\n   作品 {i}: {row[0]}")
                    if row[1]:
                        desc_preview = row[1][:100] + "..." if len(row[1]) > 100 else row[1]
                        print(f"   描述: {desc_preview}")
                    if row[2]:
                        print(f"   關係: {row[2]} → {row[3]}: {row[4]}")
            else:
                print("   ⚠️  未找到完全匹配的結果")
                # 嘗試模糊搜索
                fuzzy_response = requests.post(
                    "http://localhost:7474/db/neo4j/tx/commit",
                    auth=("neo4j", "arthistory123"),
                    json={
                        "statements": [{
                            "statement": """
                            MATCH (a:Artwork)
                            RETURN a.title as title, a.description as description
                            LIMIT 5
                            """
                        }]
                    },
                    timeout=10
                )
                if fuzzy_response.status_code == 200:
                    fuzzy_result = fuzzy_response.json()
                    print("\n   📝 可用的藝術品範例:")
                    for i, item in enumerate(fuzzy_result["results"][0]["data"], 1):
                        print(f"     {i}. {item['row'][0]}")
        else:
            print(f"   ❌ 查詢失敗: HTTP {response.status_code}")

    except Exception as e:
        print(f"   ❌ 查詢錯誤: {str(e)}")


def main():
    """主測試函數"""
    print("\n" + "="*60)
    print("🎨 OpenWebUI RAG 整合測試")
    print("="*60)

    # 測試各個組件
    neo4j_ok = test_neo4j_connection()
    chromadb_ok = test_chromadb_connection()

    if neo4j_ok:
        test_rag_query()

    # 總結
    print("\n" + "="*60)
    print("📊 測試總結")
    print("="*60)
    print(f"Neo4j 連接: {'✅ 正常' if neo4j_ok else '❌ 失敗'}")
    print(f"ChromaDB 連接: {'✅ 正常' if chromadb_ok else '❌ 失敗'}")

    if neo4j_ok and chromadb_ok:
        print("\n🎉 所有連接測試通過!")
        print("\n💡 下一步:")
        print("   1. 在 OpenWebUI 中測試查詢功能")
        print("   2. 檢查圖譜視覺化是否正常顯示")
        print("   3. 驗證多個 RAG 策略的效果")
    else:
        print("\n⚠️  部分連接測試失敗，請檢查服務配置")

    print("="*60 + "\n")


if __name__ == "__main__":
    main()
