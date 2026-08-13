#!/usr/bin/env python3
"""
將新古典主義和浪漫主義資料同步到 ChromaDB
使用嵌入模型生成向量並儲存
"""

import json
import logging
from pathlib import Path
import requests
from typing import List, Dict
import time

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ChromaDB 配置
CHROMADB_HOST = "localhost"
CHROMADB_PORT = 8000
CHROMADB_API_BASE = f"http://{CHROMADB_HOST}:{CHROMADB_PORT}/api/v1"

# Ollama 配置 (用於生成嵌入向量)
OLLAMA_HOST = "localhost"
OLLAMA_PORT = 11434
OLLAMA_API_BASE = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}"
EMBEDDING_MODEL = "nomic-embed-text"

class ChromaDBSynchronizer:
    """ChromaDB 資料同步器"""

    def __init__(self):
        self.collection_name = "art_history_neoclassical_romantic"
        self.chromadb_base = CHROMADB_API_BASE
        self.ollama_base = OLLAMA_API_BASE

    def generate_embedding(self, text: str) -> List[float]:
        """使用 Ollama 生成文本嵌入向量"""
        try:
            response = requests.post(
                f"{self.ollama_base}/api/embeddings",
                json={
                    "model": EMBEDDING_MODEL,
                    "prompt": text
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("embedding", [])
            else:
                logger.error(f"嵌入生成失敗: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"嵌入生成錯誤: {e}")
            return []

    def prepare_document_text(self, artwork: Dict) -> str:
        """準備用於嵌入的文本"""
        parts = []

        # 標題
        if artwork.get('title'):
            parts.append(f"Title: {artwork['title']}")

        # 描述
        if artwork.get('description'):
            parts.append(f"Description: {artwork['description']}")

        # 藝術家
        people = artwork.get('people', [])
        if people:
            artists = [p.get('name', '') for p in people if p.get('name')]
            if artists:
                parts.append(f"Artist: {', '.join(artists)}")

        # 時期
        if artwork.get('dated'):
            parts.append(f"Date: {artwork['dated']}")

        if artwork.get('period'):
            parts.append(f"Period: {artwork['period']}")

        # 文化
        if artwork.get('culture'):
            parts.append(f"Culture: {artwork['culture']}")

        # 分類
        if artwork.get('classification'):
            parts.append(f"Classification: {artwork['classification']}")

        return " | ".join(parts)

    def create_collection(self):
        """創建或獲取 ChromaDB 集合"""
        try:
            # 使用 ChromaDB Python 客戶端
            import chromadb

            # 連接到 ChromaDB
            client = chromadb.HttpClient(
                host=CHROMADB_HOST,
                port=CHROMADB_PORT
            )

            # 創建或獲取集合
            collection = client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Neoclassical and Romantic art history data"}
            )

            logger.info(f"✅ 集合 '{self.collection_name}' 已就緒")
            return client, collection

        except Exception as e:
            logger.error(f"❌ 創建集合失敗: {e}")
            return None, None

    def sync_artworks(self, artworks: List[Dict]):
        """同步藝術品到 ChromaDB"""
        logger.info(f"\n🚀 開始同步 {len(artworks)} 件藝術品到 ChromaDB...")

        # 創建集合
        client, collection = self.create_collection()
        if not collection:
            logger.error("❌ 無法創建集合，同步終止")
            return 0, len(artworks)

        success_count = 0
        error_count = 0

        # 批次處理
        batch_size = 10

        for i in range(0, len(artworks), batch_size):
            batch = artworks[i:i+batch_size]

            ids = []
            embeddings = []
            documents = []
            metadatas = []

            for artwork in batch:
                artwork_id = str(artwork.get('id', ''))
                if not artwork_id:
                    continue

                # 準備文本
                text = self.prepare_document_text(artwork)
                if not text:
                    continue

                # 生成嵌入向量
                embedding = self.generate_embedding(text)
                if not embedding:
                    logger.warning(f"⚠️  跳過作品 {artwork_id}: 無法生成嵌入向量")
                    error_count += 1
                    continue

                # 準備元資料 (過濾掉 None 值和空字串)
                metadata = {
                    "art_period": "Neoclassical/Romantic",
                    "source": "Harvard Art Museums"
                }

                # 只添加非空值
                if artwork.get('title'):
                    metadata["title"] = str(artwork['title'])[:500]
                if artwork.get('culture'):
                    metadata["culture"] = str(artwork['culture'])
                if artwork.get('period'):
                    metadata["period"] = str(artwork['period'])
                if artwork.get('classification'):
                    metadata["classification"] = str(artwork['classification'])
                if artwork.get('dated'):
                    metadata["dated"] = str(artwork['dated'])

                # 添加藝術家
                people = artwork.get('people', [])
                if people and people[0].get('name'):
                    metadata['artist'] = people[0]['name']

                ids.append(f"neoclassical_romantic_{artwork_id}")
                embeddings.append(embedding)
                documents.append(text)
                metadatas.append(metadata)

            # 批次插入
            if ids:
                try:
                    collection.add(
                        ids=ids,
                        embeddings=embeddings,
                        documents=documents,
                        metadatas=metadatas
                    )
                    success_count += len(ids)
                    logger.info(f"   ✅ 已同步 {success_count}/{len(artworks)} 件作品")

                    # 避免過快請求
                    time.sleep(0.5)

                except Exception as e:
                    logger.error(f"   ❌ 批次插入失敗: {e}")
                    error_count += len(ids)

        logger.info(f"\n✅ ChromaDB 同步完成!")
        logger.info(f"   成功: {success_count} 件")
        logger.info(f"   失敗: {error_count} 件")

        return success_count, error_count

    def verify_collection(self):
        """驗證 ChromaDB 集合"""
        logger.info(f"\n🔍 驗證 ChromaDB 集合...")

        try:
            import chromadb

            client = chromadb.HttpClient(
                host=CHROMADB_HOST,
                port=CHROMADB_PORT
            )

            collection = client.get_collection(name=self.collection_name)
            count = collection.count()

            logger.info(f"   ✅ 集合 '{self.collection_name}' 包含 {count} 個文檔")

            # 測試查詢
            if count > 0:
                logger.info(f"   🔍 執行測試查詢...")
                test_embedding = self.generate_embedding("neoclassical art")

                if test_embedding:
                    results = collection.query(
                        query_embeddings=[test_embedding],
                        n_results=3
                    )

                    if results and results['documents']:
                        logger.info(f"   ✅ 查詢成功，找到 {len(results['documents'][0])} 個結果")
                        logger.info(f"   📄 前 3 個結果:")
                        for i, doc in enumerate(results['documents'][0], 1):
                            preview = doc[:100] + "..." if len(doc) > 100 else doc
                            logger.info(f"      {i}. {preview}")

            return count

        except Exception as e:
            logger.error(f"   ❌ 驗證失敗: {e}")
            return 0


def check_ollama_service():
    """檢查 Ollama 服務是否運行"""
    try:
        response = requests.get(f"{OLLAMA_API_BASE}/api/tags", timeout=5)
        if response.status_code == 200:
            logger.info("✅ Ollama 服務運行正常")

            # 檢查嵌入模型是否可用
            models = response.json().get('models', [])
            model_names = [m.get('name', '') for m in models]

            if EMBEDDING_MODEL in model_names or f"{EMBEDDING_MODEL}:latest" in model_names:
                logger.info(f"✅ 嵌入模型 '{EMBEDDING_MODEL}' 可用")
                return True
            else:
                logger.warning(f"⚠️  嵌入模型 '{EMBEDDING_MODEL}' 不可用")
                logger.info(f"   可用模型: {model_names}")
                logger.info(f"   提示: 執行 'ollama pull {EMBEDDING_MODEL}' 安裝模型")
                return False
        else:
            logger.error(f"❌ Ollama 服務異常: {response.status_code}")
            return False

    except Exception as e:
        logger.error(f"❌ 無法連接到 Ollama: {e}")
        logger.info(f"   請確認 Ollama 服務正在運行 (端口 {OLLAMA_PORT})")
        return False


def check_chromadb_service():
    """檢查 ChromaDB 服務是否運行"""
    try:
        # 使用 v2 API
        response = requests.get(f"http://{CHROMADB_HOST}:{CHROMADB_PORT}/api/v2", timeout=5)
        if response.status_code == 200:
            logger.info("✅ ChromaDB 服務運行正常 (API v2)")
            return True
        else:
            logger.error(f"❌ ChromaDB 服務異常: {response.status_code}")
            return False

    except Exception as e:
        logger.error(f"❌ 無法連接到 ChromaDB: {e}")
        logger.info(f"   請確認 ChromaDB 服務正在運行 (端口 {CHROMADB_PORT})")
        return False


def main():
    """主函數"""
    print("\n" + "="*70)
    print("🎨 新古典主義與浪漫主義資料 - ChromaDB 同步")
    print("="*70)

    # 檢查服務
    logger.info("\n📋 檢查服務狀態...")
    chromadb_ok = check_chromadb_service()
    ollama_ok = check_ollama_service()

    if not chromadb_ok or not ollama_ok:
        logger.error("\n❌ 服務檢查失敗，無法繼續同步")
        return

    # 尋找資料檔案
    data_dir = Path("./comprehensive_art_data/neoclassical_romantic")
    json_files = sorted(data_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)

    if not json_files:
        logger.error("❌ 找不到資料檔案！")
        return

    json_file = json_files[0]
    logger.info(f"\n📁 使用資料檔案: {json_file}")

    # 讀取資料
    with open(json_file, 'r', encoding='utf-8') as f:
        artworks = json.load(f)

    logger.info(f"📦 共有 {len(artworks)} 件藝術品待同步")

    # 執行同步
    synchronizer = ChromaDBSynchronizer()
    success, errors = synchronizer.sync_artworks(artworks)

    # 驗證結果
    count = synchronizer.verify_collection()

    # 總結
    print("\n" + "="*70)
    print("📊 同步總結")
    print("="*70)
    print(f"ChromaDB 同步成功: {success} 件")
    print(f"ChromaDB 同步失敗: {errors} 件")
    print(f"ChromaDB 驗證結果: {count} 個文檔")
    print(f"集合名稱: {synchronizer.collection_name}")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
