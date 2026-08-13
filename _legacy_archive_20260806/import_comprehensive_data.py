#!/usr/bin/env python3
"""
綜合藝術史資料匯入腳本
將爬取的資料匯入Neo4j和ChromaDB
"""

import json
import logging
import sys
from pathlib import Path
from typing import List, Dict
import time

# 添加langchain-rag目錄到路徑
langchain_rag_dir = Path(__file__).parent / "langchain-rag"
sys.path.insert(0, str(langchain_rag_dir))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from neo4j import GraphDatabase
    import chromadb
    from chromadb.config import Settings
    import requests
except ImportError as e:
    logger.error(f"缺少必要的套件: {e}")
    logger.info("請安裝: pip install neo4j chromadb requests")
    sys.exit(1)


class ComprehensiveDataImporter:
    """綜合資料匯入器"""

    def __init__(self, data_dir="./comprehensive_art_data"):
        self.data_dir = Path(data_dir)

        # Neo4j 配置
        self.neo4j_uri = "bolt://localhost:7687"
        self.neo4j_user = "neo4j"
        self.neo4j_password = "arthistory123"

        # ChromaDB 配置
        self.chroma_host = "localhost"
        self.chroma_port = 8001
        self.collection_name = "art_history_collection"

        # Ollama 配置（用於生成嵌入）
        self.ollama_url = "http://localhost:11434"
        self.embedding_model = "nomic-embed-text"

    def connect_neo4j(self):
        """連接Neo4j"""
        try:
            driver = GraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_user, self.neo4j_password)
            )
            # 測試連接
            with driver.session() as session:
                result = session.run("RETURN 1")
                result.single()
            logger.info("✅ 成功連接 Neo4j")
            return driver
        except Exception as e:
            logger.error(f"❌ Neo4j 連接失敗: {e}")
            return None

    def connect_chromadb(self):
        """連接ChromaDB"""
        try:
            client = chromadb.HttpClient(
                host=self.chroma_host,
                port=self.chroma_port
            )
            # 獲取或創建collection
            collection = client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Art History Collection with comprehensive periods"}
            )
            logger.info("✅ 成功連接 ChromaDB")
            return client, collection
        except Exception as e:
            logger.error(f"❌ ChromaDB 連接失敗: {e}")
            return None, None

    def generate_embedding(self, text: str) -> List[float]:
        """使用Ollama生成嵌入向量"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/embeddings",
                json={
                    "model": self.embedding_model,
                    "prompt": text
                },
                timeout=30
            )

            if response.status_code == 200:
                return response.json()['embedding']
            else:
                logger.warning(f"⚠️ 嵌入生成失敗: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"❌ 生成嵌入異常: {e}")
            return None

    def import_to_neo4j(self, neo4j_driver, period_id: str, objects: List[Dict]):
        """匯入資料到Neo4j"""
        logger.info(f"\n📊 匯入 {period_id} 到 Neo4j...")

        imported_count = 0
        skipped_count = 0

        with neo4j_driver.session() as session:
            for obj in objects:
                try:
                    # 提取作品資訊
                    artwork_data = self._extract_artwork_data(obj, period_id)

                    if not artwork_data:
                        skipped_count += 1
                        continue

                    # 創建Artwork節點
                    session.run("""
                        MERGE (a:Artwork {objectID: $objectID})
                        SET a.title = $title,
                            a.period = $period,
                            a.dated = $dated,
                            a.culture = $culture,
                            a.medium = $medium,
                            a.dimensions = $dimensions,
                            a.classification = $classification,
                            a.department = $department,
                            a.description = $description,
                            a.image_url = $image_url,
                            a.original_source = $source,
                            a.updated_at = datetime()
                    """, **artwork_data)

                    # 處理藝術家
                    artist_name = artwork_data.get('artist_name')
                    if artist_name:
                        session.run("""
                            MERGE (artist:Artist {name: $name})
                            SET artist.period = $period,
                                artist.updated_at = datetime()
                            WITH artist
                            MATCH (a:Artwork {objectID: $objectID})
                            MERGE (artist)-[:CREATED]->(a)
                        """, name=artist_name, period=period_id, objectID=artwork_data['objectID'])

                    imported_count += 1

                    if imported_count % 100 == 0:
                        logger.info(f"   已匯入 {imported_count} 件作品...")

                except Exception as e:
                    logger.warning(f"⚠️ 匯入作品失敗: {e}")
                    skipped_count += 1
                    continue

        logger.info(f"✅ Neo4j匯入完成: {imported_count} 件成功, {skipped_count} 件跳過")
        return imported_count

    def import_to_chromadb(self, collection, period_id: str, objects: List[Dict]):
        """匯入資料到ChromaDB"""
        logger.info(f"\n📊 匯入 {period_id} 到 ChromaDB...")

        imported_count = 0
        batch_size = 50
        batch_ids = []
        batch_documents = []
        batch_metadatas = []
        batch_embeddings = []

        for idx, obj in enumerate(objects):
            try:
                # 提取作品資訊
                artwork_data = self._extract_artwork_data(obj, period_id)

                if not artwork_data:
                    continue

                # 生成文檔文本
                doc_text = self._generate_document_text(artwork_data)

                # 生成嵌入
                embedding = self.generate_embedding(doc_text)

                if not embedding:
                    continue

                # 添加到批次
                batch_ids.append(f"{period_id}_{artwork_data['objectID']}")
                batch_documents.append(doc_text)
                batch_metadatas.append({
                    'period': period_id,
                    'title': artwork_data['title'][:200],
                    'artist': artwork_data.get('artist_name', 'Unknown')[:100],
                    'source': artwork_data.get('source', 'Unknown')
                })
                batch_embeddings.append(embedding)

                # 當批次達到大小時，寫入ChromaDB
                if len(batch_ids) >= batch_size:
                    collection.add(
                        ids=batch_ids,
                        documents=batch_documents,
                        metadatas=batch_metadatas,
                        embeddings=batch_embeddings
                    )
                    imported_count += len(batch_ids)
                    logger.info(f"   已匯入 {imported_count} 件作品...")

                    # 清空批次
                    batch_ids = []
                    batch_documents = []
                    batch_metadatas = []
                    batch_embeddings = []

                    time.sleep(0.5)  # 避免過載

            except Exception as e:
                logger.warning(f"⚠️ ChromaDB匯入失敗: {e}")
                continue

        # 匯入剩餘的批次
        if batch_ids:
            try:
                collection.add(
                    ids=batch_ids,
                    documents=batch_documents,
                    metadatas=batch_metadatas,
                    embeddings=batch_embeddings
                )
                imported_count += len(batch_ids)
            except Exception as e:
                logger.warning(f"⚠️ 最後批次匯入失敗: {e}")

        logger.info(f"✅ ChromaDB匯入完成: {imported_count} 件")
        return imported_count

    def _extract_artwork_data(self, obj: Dict, period_id: str) -> Dict:
        """提取作品資料（兼容Harvard和Met格式）"""
        # Harvard Art Museums 格式
        if 'id' in obj and 'title' in obj:
            return {
                'objectID': str(obj.get('id')),
                'title': obj.get('title', 'Untitled'),
                'artist_name': obj.get('people', [{}])[0].get('name') if obj.get('people') else None,
                'dated': obj.get('dated', ''),
                'period': period_id,
                'culture': obj.get('culture', ''),
                'medium': obj.get('medium', ''),
                'dimensions': obj.get('dimensions', ''),
                'classification': obj.get('classification', ''),
                'department': obj.get('department', ''),
                'description': obj.get('description', ''),
                'image_url': obj.get('primaryimageurl', ''),
                'source': 'Harvard Art Museums'
            }

        # Met Museum 格式
        elif 'objectID' in obj:
            return {
                'objectID': str(obj.get('objectID')),
                'title': obj.get('title', 'Untitled'),
                'artist_name': obj.get('artistDisplayName'),
                'dated': obj.get('objectDate', ''),
                'period': period_id,
                'culture': obj.get('culture', ''),
                'medium': obj.get('medium', ''),
                'dimensions': obj.get('dimensions', ''),
                'classification': obj.get('classification', ''),
                'department': obj.get('department', ''),
                'description': obj.get('objectName', ''),
                'image_url': obj.get('primaryImage', ''),
                'source': 'Met Museum'
            }

        return None

    def _generate_document_text(self, artwork_data: Dict) -> str:
        """生成ChromaDB文檔文本"""
        parts = []

        if artwork_data.get('title'):
            parts.append(f"標題: {artwork_data['title']}")

        if artwork_data.get('artist_name'):
            parts.append(f"藝術家: {artwork_data['artist_name']}")

        if artwork_data.get('dated'):
            parts.append(f"年代: {artwork_data['dated']}")

        if artwork_data.get('period'):
            parts.append(f"時期: {artwork_data['period']}")

        if artwork_data.get('culture'):
            parts.append(f"文化: {artwork_data['culture']}")

        if artwork_data.get('medium'):
            parts.append(f"媒材: {artwork_data['medium']}")

        if artwork_data.get('description'):
            parts.append(f"描述: {artwork_data['description']}")

        return ". ".join(parts)

    def import_all_periods(self):
        """匯入所有時期的資料"""
        logger.info("🚀 開始匯入綜合藝術史資料")
        logger.info("="*60)

        # 連接資料庫
        neo4j_driver = self.connect_neo4j()
        chroma_client, chroma_collection = self.connect_chromadb()

        if not neo4j_driver:
            logger.error("❌ 無法連接Neo4j，請確認Docker容器運行中")
            return

        if not chroma_collection:
            logger.error("❌ 無法連接ChromaDB，請確認Docker容器運行中")
            return

        # 查找所有時期的資料檔案
        period_files = list(self.data_dir.glob("*_artworks.json"))

        if not period_files:
            logger.error(f"❌ 在 {self.data_dir} 找不到資料檔案")
            logger.info("請先運行: python3 comprehensive_art_history_crawler.py")
            return

        logger.info(f"找到 {len(period_files)} 個時期的資料檔案")

        total_stats = {
            'neo4j_imported': 0,
            'chromadb_imported': 0
        }

        # 匯入每個時期
        for period_file in period_files:
            period_id = period_file.stem.replace('_artworks', '')

            logger.info(f"\n{'='*60}")
            logger.info(f"處理時期: {period_id}")
            logger.info(f"{'='*60}")

            # 讀取資料
            with open(period_file, 'r', encoding='utf-8') as f:
                objects = json.load(f)

            logger.info(f"載入 {len(objects)} 件作品")

            # 匯入到Neo4j
            neo4j_count = self.import_to_neo4j(neo4j_driver, period_id, objects)
            total_stats['neo4j_imported'] += neo4j_count

            # 匯入到ChromaDB
            chroma_count = self.import_to_chromadb(chroma_collection, period_id, objects)
            total_stats['chromadb_imported'] += chroma_count

        # 關閉連接
        neo4j_driver.close()

        # 生成總結報告
        logger.info(f"\n{'='*60}")
        logger.info("📊 匯入總結")
        logger.info(f"{'='*60}")
        logger.info(f"Neo4j 匯入: {total_stats['neo4j_imported']} 件")
        logger.info(f"ChromaDB 匯入: {total_stats['chromadb_imported']} 件")
        logger.info(f"{'='*60}")

        logger.info("\n✅ 資料匯入完成！")
        logger.info("\n💡 下一步:")
        logger.info("1. 在OpenWebUI測試新資料: http://localhost:8080")
        logger.info("2. 使用系統狀態檢查: bash check_system_status.sh")


def main():
    print("\n🎨 綜合藝術史資料匯入工具")
    print("="*60)

    data_dir = input("資料目錄（按Enter使用默認: ./comprehensive_art_data）: ").strip()
    if not data_dir:
        data_dir = "./comprehensive_art_data"

    confirm = input(f"\n確認開始匯入？(y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ 已取消")
        return

    importer = ComprehensiveDataImporter(data_dir=data_dir)
    importer.import_all_periods()

    print("\n✅ 匯入完成！")


if __name__ == "__main__":
    main()
