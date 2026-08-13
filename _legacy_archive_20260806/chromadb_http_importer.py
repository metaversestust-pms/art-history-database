#!/usr/bin/env python3
"""
使用HTTP API直接導入資料到ChromaDB（無需chromadb套件）
"""

import json
import logging
import requests
from pathlib import Path
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ChromaDBHTTPImporter:
    """使用HTTP API的ChromaDB導入器"""

    def __init__(self, host='localhost', port=8001):
        self.base_url = f"http://{host}:{port}"
        self.tenant = "default_tenant"
        self.database = "default_database"
        self.collection_name = "renaissance_baroque_art"

    def check_connection(self):
        """檢查ChromaDB連接"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/heartbeat")
            logger.info(f"✅ ChromaDB服務連接成功")
            return True
        except Exception as e:
            logger.error(f"❌ ChromaDB服務連接失敗: {e}")
            return False

    def delete_collection(self):
        """刪除現有集合"""
        try:
            response = requests.post(
                f"{self.base_url}/collections/{self.collection_name}/delete",
                json={}
            )
            if response.status_code in [200, 404]:
                logger.info(f"🗑️ 已刪除舊集合（如果存在）")
                return True
        except Exception as e:
            logger.warning(f"刪除集合時出錯（可能不存在）: {e}")
            return True

    def create_collection(self):
        """創建新集合"""
        try:
            response = requests.post(
                f"{self.base_url}/collections",
                json={
                    "name": self.collection_name,
                    "metadata": {
                        "description": "Renaissance and Baroque Art Collection"
                    }
                }
            )
            if response.status_code in [200, 201]:
                logger.info(f"✨ 成功創建集合: {self.collection_name}")
                return True
            else:
                logger.error(f"創建集合失敗: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"創建集合異常: {e}")
            return False

    def add_documents_batch(self, documents, metadatas, ids):
        """批量添加文檔"""
        try:
            # ChromaDB API v1 格式
            payload = {
                "ids": ids,
                "documents": documents,
                "metadatas": metadatas
            }

            response = requests.post(
                f"{self.base_url}/collections/{self.collection_name}/add",
                json=payload,
                timeout=60
            )

            if response.status_code in [200, 201]:
                return True
            else:
                logger.warning(f"批量添加失敗: {response.status_code} - {response.text[:200]}")
                return False
        except Exception as e:
            logger.error(f"批量添加異常: {e}")
            return False

    def get_collection_count(self):
        """獲取集合中的文檔數量"""
        try:
            response = requests.get(
                f"{self.base_url}/collections/{self.collection_name}/count"
            )
            if response.status_code == 200:
                return response.json()
            return 0
        except Exception as e:
            logger.warning(f"獲取計數失敗: {e}")
            return 0

    def process_artworks(self, artworks):
        """處理並導入藝術作品"""
        logger.info(f"📥 準備處理 {len(artworks)} 件藝術作品...")

        documents = []
        metadatas = []
        ids = []

        for artwork in artworks:
            artwork_id = str(artwork.get('id', ''))
            title = artwork.get('title', 'Untitled')
            description = artwork.get('description', '')
            medium = artwork.get('medium', '')
            culture = artwork.get('culture', '')
            classification = artwork.get('classification', '')
            dated = artwork.get('dated', '')

            # 判斷時期
            text = f"{title} {description} {culture}".lower()
            if any(kw in text for kw in ['renaissance', 'raphael', 'leonardo', 'michelangelo']):
                period = 'Renaissance'
            elif any(kw in text for kw in ['baroque', 'caravaggio', 'rembrandt', 'rubens']):
                period = 'Baroque'
            else:
                period = 'Unknown'

            # 提取藝術家
            artist_names = []
            if 'people' in artwork and artwork['people']:
                for person in artwork['people']:
                    if person.get('role') in ['Artist', 'Creator', 'Maker']:
                        artist_names.append(person.get('name', ''))

            artist_str = ', '.join(artist_names) if artist_names else 'Unknown'

            # 組合文本
            text_parts = [
                f"Title: {title}",
                f"Period: {period}",
                f"Artist: {artist_str}",
                f"Dated: {dated}" if dated else "",
                f"Medium: {medium}" if medium else "",
                f"Culture: {culture}" if culture else "",
                f"Classification: {classification}" if classification else "",
                f"Description: {description}" if description else ""
            ]

            text = " | ".join([part for part in text_parts if part])[:2000]

            documents.append(text)
            metadatas.append({
                'title': title[:200],
                'artist': artist_str[:200],
                'period': period,
                'dated': dated[:100],
                'medium': medium[:200],
                'culture': culture[:100],
                'classification': classification[:100],
                'source': 'Harvard Art Museums'
            })
            ids.append(f"renaissance_baroque_{artwork_id}")

        return documents, metadatas, ids

    def run_import(self, data_file):
        """執行完整的導入流程"""
        logger.info("🚀 開始ChromaDB HTTP導入流程...")

        # 1. 檢查連接
        if not self.check_connection():
            return False

        # 2. 載入資料
        logger.info(f"📁 載入資料: {data_file}")
        with open(data_file, 'r', encoding='utf-8') as f:
            artworks = json.load(f)
        logger.info(f"✅ 成功載入 {len(artworks)} 件作品")

        # 3. 刪除舊集合並創建新集合
        self.delete_collection()
        time.sleep(2)  # 等待刪除完成

        if not self.create_collection():
            return False

        time.sleep(2)  # 等待集合創建完成

        # 4. 處理資料
        documents, metadatas, ids = self.process_artworks(artworks)

        # 5. 批量添加（每批50個）
        batch_size = 50
        successful = 0
        failed = 0

        logger.info(f"📥 開始批量添加文檔（批次大小: {batch_size}）...")

        for i in range(0, len(documents), batch_size):
            batch_docs = documents[i:i+batch_size]
            batch_metas = metadatas[i:i+batch_size]
            batch_ids = ids[i:i+batch_size]

            if self.add_documents_batch(batch_docs, batch_metas, batch_ids):
                successful += len(batch_docs)
                logger.info(f"  ✓ 進度: {min(i+batch_size, len(documents))}/{len(documents)} ({successful}成功)")
            else:
                failed += len(batch_docs)
                logger.warning(f"  ✗ 批次 {i}-{i+batch_size} 失敗")

            time.sleep(0.5)  # 避免過快請求

        # 6. 驗證結果
        time.sleep(2)
        count = self.get_collection_count()

        logger.info(f"\n{'='*60}")
        logger.info(f"🎉 ChromaDB導入完成！")
        logger.info(f"{'='*60}")
        logger.info(f"   集合名稱: {self.collection_name}")
        logger.info(f"   成功添加: {successful} 個文檔")
        logger.info(f"   失敗: {failed} 個文檔")
        logger.info(f"   集合計數: {count}")

        return successful > 0

def main():
    """主函數"""
    print("\n🎨 ChromaDB HTTP 導入器")
    print("="*60)
    print("使用HTTP API直接與ChromaDB通信（無需chromadb套件）")
    print("="*60)

    # 設定資料檔案路徑
    data_file = Path("./renaissance_baroque_data/combined_renaissance_baroque.json")

    if not data_file.exists():
        print(f"❌ 找不到資料檔案: {data_file}")
        return

    # 創建導入器並執行
    importer = ChromaDBHTTPImporter()
    success = importer.run_import(data_file)

    if success:
        print("\n✅ 資料已成功導入ChromaDB！")
        print("\n💡 下一步：")
        print("  1. 在OpenWebUI中測試RAG查詢")
        print("  2. 提問關於文藝復興和巴洛克時期的問題")
    else:
        print("\n❌ 導入過程遇到問題，請檢查日誌")

if __name__ == "__main__":
    main()
