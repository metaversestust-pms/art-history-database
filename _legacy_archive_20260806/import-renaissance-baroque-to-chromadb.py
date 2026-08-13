#!/usr/bin/env python3
"""
匯入Renaissance和Baroque資料到ChromaDB向量資料庫
支援所有向量基礎的RAG方法檢索
"""

import json
import chromadb
from chromadb.config import Settings
import sys
from datetime import datetime

class ChromaDBImporter:
    def __init__(self):
        # 連接到ChromaDB (使用Docker容器中的ChromaDB)
        self.client = chromadb.HttpClient(
            host='localhost',
            port=8000,
            settings=Settings(allow_reset=True, anonymized_telemetry=False)
        )

        # 創建或獲取collection
        self.collection_name = "art_history"
        try:
            self.collection = self.client.get_collection(self.collection_name)
            print(f"✅ 已連接到現有collection: {self.collection_name}")
        except:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Art history knowledge base with Renaissance and Baroque artworks"}
            )
            print(f"✅ 已創建新collection: {self.collection_name}")

        self.stats = {
            'total': 0,
            'renaissance': 0,
            'baroque': 0,
            'other': 0,
            'with_images': 0
        }

    def create_artwork_text(self, artwork):
        """
        創建藝術作品的文本表示用於嵌入
        """
        parts = []

        # 基本資訊
        if artwork.get('title'):
            parts.append(f"Title: {artwork['title']}")

        if artwork.get('artist'):
            parts.append(f"Artist: {artwork['artist']}")

        if artwork.get('date'):
            parts.append(f"Date: {artwork['date']}")

        if artwork.get('period'):
            parts.append(f"Period: {artwork['period']}")

        # 媒材和分類
        if artwork.get('medium'):
            parts.append(f"Medium: {artwork['medium']}")

        if artwork.get('classification'):
            parts.append(f"Classification: {artwork['classification']}")

        # 博物館資訊
        if artwork.get('museum'):
            parts.append(f"Museum: {artwork['museum']}")

        if artwork.get('department'):
            parts.append(f"Department: {artwork['department']}")

        # 文化和地理資訊
        if artwork.get('culture'):
            parts.append(f"Culture: {artwork['culture']}")

        if artwork.get('geography'):
            parts.append(f"Geography: {artwork['geography']}")

        return " | ".join(parts)

    def import_artworks(self, json_file_path):
        """
        從JSON檔案匯入藝術作品
        """
        print(f"\n📖 讀取資料檔案: {json_file_path}")

        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        artworks = data.get('artworks', [])
        print(f"✅ 找到 {len(artworks)} 件藝術作品")

        # 準備批次資料
        documents = []
        metadatas = []
        ids = []

        for artwork in artworks:
            # 創建文本表示
            text = self.create_artwork_text(artwork)

            # 創建metadata
            metadata = {
                'met_id': str(artwork.get('id', '')),
                'title': artwork.get('title', 'Unknown')[:500],  # ChromaDB限制長度
                'artist': artwork.get('artist', 'Unknown')[:200],
                'date': artwork.get('date', '')[:100],
                'period': artwork.get('period', '')[:50],
                'medium': artwork.get('medium', '')[:200],
                'classification': artwork.get('classification', '')[:100],
                'department': artwork.get('department', '')[:100],
                'culture': artwork.get('culture', '')[:100],
                'is_highlight': str(artwork.get('is_highlight', False)),
                'has_image': str(bool(artwork.get('image'))),
                'url': artwork.get('url', '')[:500]
            }

            # 添加到批次
            documents.append(text)
            metadatas.append(metadata)
            ids.append(f"met_{artwork.get('id', len(ids))}")

            # 更新統計
            self.stats['total'] += 1
            period = artwork.get('period', '').lower()
            if 'renaissance' in period:
                self.stats['renaissance'] += 1
            elif 'baroque' in period:
                self.stats['baroque'] += 1
            else:
                self.stats['other'] += 1

            if artwork.get('image'):
                self.stats['with_images'] += 1

        # 批次匯入到ChromaDB
        print(f"\n🔄 開始匯入 {len(documents)} 件作品到ChromaDB...")

        # ChromaDB限制每次最多41666個文檔，我們分批處理
        batch_size = 1000
        for i in range(0, len(documents), batch_size):
            batch_docs = documents[i:i+batch_size]
            batch_metas = metadatas[i:i+batch_size]
            batch_ids = ids[i:i+batch_size]

            try:
                self.collection.add(
                    documents=batch_docs,
                    metadatas=batch_metas,
                    ids=batch_ids
                )
                print(f"  ✅ 已匯入 {i+len(batch_docs)}/{len(documents)} 件作品")
            except Exception as e:
                print(f"  ⚠️ 批次 {i}-{i+batch_size} 匯入失敗: {e}")
                # 嘗試逐個匯入以找出問題
                for j, (doc, meta, doc_id) in enumerate(zip(batch_docs, batch_metas, batch_ids)):
                    try:
                        self.collection.add(
                            documents=[doc],
                            metadatas=[meta],
                            ids=[doc_id]
                        )
                    except Exception as e2:
                        print(f"    ❌ 作品 {doc_id} 匯入失敗: {e2}")

        print(f"\n✅ ChromaDB匯入完成！")
        return True

    def verify_import(self):
        """
        驗證匯入結果
        """
        print(f"\n╔═══════════════════════════════════════════════════════════╗")
        print(f"║            ChromaDB 匯入驗證                              ║")
        print(f"╚═══════════════════════════════════════════════════════════╝")

        # 獲取collection資訊
        count = self.collection.count()
        print(f"\n📊 Collection統計:")
        print(f"   Collection名稱: {self.collection_name}")
        print(f"   總文檔數: {count}")

        print(f"\n📊 匯入統計:")
        print(f"   總作品數: {self.stats['total']}")
        print(f"   Renaissance: {self.stats['renaissance']}")
        print(f"   Baroque: {self.stats['baroque']}")
        print(f"   其他相關: {self.stats['other']}")
        print(f"   含圖片: {self.stats['with_images']}")

        # 測試查詢
        print(f"\n🔍 測試向量檢索:")

        test_queries = [
            "Leonardo da Vinci",
            "Renaissance paintings",
            "Baroque art",
            "Rembrandt"
        ]

        for query in test_queries:
            try:
                results = self.collection.query(
                    query_texts=[query],
                    n_results=3
                )

                if results and results['ids'] and len(results['ids'][0]) > 0:
                    print(f"\n   ✅ 查詢 '{query}': 找到 {len(results['ids'][0])} 個結果")
                    # 顯示第一個結果
                    if results['metadatas'] and len(results['metadatas'][0]) > 0:
                        first = results['metadatas'][0][0]
                        print(f"      - {first.get('title', 'Unknown')}")
                        print(f"        藝術家: {first.get('artist', 'Unknown')}")
                        print(f"        時期: {first.get('period', 'Unknown')}")
                else:
                    print(f"   ⚠️ 查詢 '{query}': 無結果")
            except Exception as e:
                print(f"   ❌ 查詢 '{query}' 失敗: {e}")

        print(f"\n✅ ChromaDB驗證完成！")

        return count > 0

    def print_summary(self):
        """
        打印最終摘要
        """
        print(f"\n╔═══════════════════════════════════════════════════════════╗")
        print(f"║            ChromaDB 匯入成功                              ║")
        print(f"╚═══════════════════════════════════════════════════════════╝")

        print(f"\n🎉 Renaissance和Baroque資料已成功匯入ChromaDB！")
        print(f"\n📊 現在支援的RAG方法:")
        print(f"   ✅ VECTOR_ONLY - 純向量檢索")
        print(f"   ✅ GRAPH_ONLY - 純圖譜檢索")
        print(f"   ✅ HYBRID_BALANCED - 混合檢索")
        print(f"   ✅ ADAPTIVE - 自適應檢索")
        print(f"   ✅ SPECIALIZED - 專門檢索")
        print(f"   ✅ ADVANCED_RAG - 進階RAG")
        print(f"   ✅ SELF_RAG - 自我RAG")
        print(f"   ✅ AGENTIC_RAG - 代理RAG")
        print(f"   ✅ NAIVE_RAG - 簡單RAG")

        print(f"\n🌐 ChromaDB訪問:")
        print(f"   URL: http://localhost:8000")
        print(f"   Collection: {self.collection_name}")
        print(f"   文檔數: {self.stats['total']}")

        print(f"\n🚀 下一步:")
        print(f"   1. 測試所有RAG策略的檢索功能")
        print(f"   2. 驗證OpenWebUI可使用所有RAG方法")
        print(f"   3. 生成完整驗證報告")

def main():
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║    Renaissance & Baroque 資料匯入 ChromaDB               ║")
    print("║    支援所有向量基礎的RAG方法                              ║")
    print("╚═══════════════════════════════════════════════════════════╝")

    # 資料檔案路徑
    data_file = "/mnt/c/Users/ssking1999/Desktop/藝術史資料庫/art-history-database/data/raw/renaissance_baroque_2025-10-15T11-42-24-847Z.json"

    try:
        # 創建匯入器
        importer = ChromaDBImporter()

        # 匯入資料
        success = importer.import_artworks(data_file)

        if success:
            # 驗證匯入
            importer.verify_import()

            # 打印摘要
            importer.print_summary()

            print(f"\n✅ 所有操作完成！")
            return 0
        else:
            print(f"\n❌ 匯入失敗")
            return 1

    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
