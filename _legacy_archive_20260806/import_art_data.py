#!/usr/bin/env python3
"""
藝術史資料導入腳本
將爬取的資料導入到 Neo4j 和 ChromaDB
"""

import json
import os
import logging
from typing import List, Dict, Any
from datetime import datetime
import hashlib

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Neo4j 和 ChromaDB 配置
try:
    from neo4j import GraphDatabase
    import chromadb
    from chromadb.config import Settings
except ImportError:
    logger.error("請先安裝依賴: pip install neo4j chromadb")
    exit(1)


class ArtDataImporter:
    """藝術資料導入器"""

    def __init__(
        self,
        neo4j_uri: str = None,
        neo4j_user: str = None,
        neo4j_password: str = None,
        chromadb_host: str = None,
        chromadb_port: int = None
    ):
        """初始化導入器"""
        # 從環境變數獲取配置，或使用默認值
        neo4j_uri = neo4j_uri or os.getenv("NEO4J_URI", "bolt://art-history-neo4j:7687")
        neo4j_user = neo4j_user or os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = neo4j_password or os.getenv("NEO4J_PASSWORD", "arthistory123")
        chromadb_host = chromadb_host or os.getenv("CHROMADB_HOST", "art-history-chromadb")
        chromadb_port = chromadb_port or int(os.getenv("CHROMADB_PORT", "8000"))
        """初始化導入器"""
        # Neo4j 連接
        self.neo4j_driver = GraphDatabase.driver(
            neo4j_uri,
            auth=(neo4j_user, neo4j_password)
        )
        logger.info(f"✅ 已連接到 Neo4j: {neo4j_uri}")

        # ChromaDB 連接
        self.chroma_client = chromadb.HttpClient(
            host=chromadb_host,
            port=chromadb_port,
            settings=Settings(allow_reset=True)
        )
        logger.info(f"✅ 已連接到 ChromaDB: {chromadb_host}:{chromadb_port}")

        # 創建或獲取 collection
        try:
            self.collection = self.chroma_client.get_or_create_collection(
                name="art_history",
                metadata={"description": "藝術史知識庫"}
            )
            logger.info("✅ ChromaDB collection 'art_history' 已準備")
        except Exception as e:
            logger.error(f"❌ 無法創建 ChromaDB collection: {e}")
            raise

    def close(self):
        """關閉連接"""
        self.neo4j_driver.close()
        logger.info("✅ 已關閉所有連接")

    def load_json_files(self, data_dir: str = "./data/raw") -> List[Dict[str, Any]]:
        """載入所有 JSON 資料文件"""
        all_artworks = []

        for filename in os.listdir(data_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(data_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            all_artworks.extend(data)
                            logger.info(f"✅ 載入 {filename}: {len(data)} 件作品")
                        elif isinstance(data, dict):
                            all_artworks.append(data)
                            logger.info(f"✅ 載入 {filename}: 1 件作品")
                except Exception as e:
                    logger.warning(f"⚠️ 無法載入 {filename}: {e}")

        logger.info(f"📊 總共載入 {len(all_artworks)} 件藝術品")
        return all_artworks

    def create_neo4j_constraints(self):
        """創建 Neo4j 約束和索引"""
        constraints = [
            "CREATE CONSTRAINT artwork_id IF NOT EXISTS FOR (a:Artwork) REQUIRE a.id IS UNIQUE",
            "CREATE CONSTRAINT artist_name IF NOT EXISTS FOR (a:Artist) REQUIRE a.name IS UNIQUE",
            "CREATE INDEX artwork_title IF NOT EXISTS FOR (a:Artwork) ON (a.title)",
            "CREATE INDEX artwork_date IF NOT EXISTS FOR (a:Artwork) ON (a.date)",
        ]

        with self.neo4j_driver.session() as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                    logger.info(f"✅ 創建約束/索引成功")
                except Exception as e:
                    logger.debug(f"約束/索引可能已存在: {e}")

    def import_to_neo4j(self, artworks: List[Dict[str, Any]]) -> int:
        """導入資料到 Neo4j"""
        logger.info("🔄 開始導入到 Neo4j...")

        # 創建約束
        self.create_neo4j_constraints()

        imported_count = 0

        with self.neo4j_driver.session() as session:
            for artwork in artworks:
                try:
                    # 創建藝術品節點
                    query = """
                    MERGE (a:Artwork {id: $id})
                    SET a.title = $title,
                        a.date = $date,
                        a.medium = $medium,
                        a.department = $department,
                        a.culture = $culture,
                        a.period = $period,
                        a.dimensions = $dimensions,
                        a.classification = $classification,
                        a.primaryImage = $primaryImage,
                        a.objectURL = $objectURL,
                        a.source = $source,
                        a.updated_at = datetime()

                    // 創建藝術家節點和關係
                    WITH a
                    MERGE (artist:Artist {name: $artist})
                    MERGE (artist)-[:CREATED]->(a)

                    // 創建來源節點
                    WITH a
                    MERGE (source:Source {name: $source})
                    MERGE (a)-[:FROM_SOURCE]->(source)

                    RETURN a.id as id
                    """

                    result = session.run(query,
                        id=str(artwork.get('id', f"unknown_{imported_count}")),
                        title=artwork.get('title', 'Unknown'),
                        artist=artwork.get('artist', 'Unknown'),
                        date=artwork.get('date', ''),
                        medium=artwork.get('medium', ''),
                        department=artwork.get('department', ''),
                        culture=artwork.get('culture', ''),
                        period=artwork.get('period', ''),
                        dimensions=artwork.get('dimensions', ''),
                        classification=artwork.get('classification', ''),
                        primaryImage=artwork.get('primaryImage', ''),
                        objectURL=artwork.get('objectURL', ''),
                        source=artwork.get('source', 'Unknown')
                    )

                    imported_count += 1

                    if imported_count % 100 == 0:
                        logger.info(f"   已導入 {imported_count} 件作品到 Neo4j...")

                except Exception as e:
                    logger.warning(f"⚠️ 導入作品失敗 ({artwork.get('id')}): {e}")

        logger.info(f"✅ Neo4j 導入完成: {imported_count} 件作品")
        return imported_count

    def generate_artwork_text(self, artwork: Dict[str, Any]) -> str:
        """生成藝術品的文本描述（用於向量嵌入）"""
        parts = []

        if artwork.get('title'):
            parts.append(f"標題: {artwork['title']}")

        if artwork.get('artist'):
            parts.append(f"藝術家: {artwork['artist']}")

        if artwork.get('date'):
            parts.append(f"創作時間: {artwork['date']}")

        if artwork.get('medium'):
            parts.append(f"媒材: {artwork['medium']}")

        if artwork.get('culture'):
            parts.append(f"文化: {artwork['culture']}")

        if artwork.get('period'):
            parts.append(f"時期: {artwork['period']}")

        if artwork.get('classification'):
            parts.append(f"分類: {artwork['classification']}")

        if artwork.get('department'):
            parts.append(f"部門: {artwork['department']}")

        return " | ".join(parts)

    def import_to_chromadb(self, artworks: List[Dict[str, Any]]) -> int:
        """導入資料到 ChromaDB"""
        logger.info("🔄 開始導入到 ChromaDB...")

        ids = []
        documents = []
        metadatas = []

        for i, artwork in enumerate(artworks):
            # 生成唯一 ID
            artwork_id = str(artwork.get('id', f'artwork_{i}'))

            # 生成文本描述
            text = self.generate_artwork_text(artwork)

            # 準備元數據
            metadata = {
                'title': artwork.get('title', 'Unknown')[:500],  # ChromaDB 限制
                'artist': artwork.get('artist', 'Unknown')[:500],
                'date': artwork.get('date', '')[:100],
                'source': artwork.get('source', 'Unknown')[:100],
                'medium': artwork.get('medium', '')[:200],
                'classification': artwork.get('classification', '')[:100]
            }

            ids.append(artwork_id)
            documents.append(text)
            metadatas.append(metadata)

        # 批量導入（ChromaDB 建議批量操作）
        batch_size = 100
        imported_count = 0

        for i in range(0, len(ids), batch_size):
            batch_ids = ids[i:i+batch_size]
            batch_docs = documents[i:i+batch_size]
            batch_metas = metadatas[i:i+batch_size]

            try:
                self.collection.add(
                    ids=batch_ids,
                    documents=batch_docs,
                    metadatas=batch_metas
                )
                imported_count += len(batch_ids)
                logger.info(f"   已導入 {imported_count} 件作品到 ChromaDB...")
            except Exception as e:
                logger.warning(f"⚠️ 批次導入失敗: {e}")

        logger.info(f"✅ ChromaDB 導入完成: {imported_count} 件作品")
        return imported_count

    def verify_import(self):
        """驗證導入結果"""
        logger.info("🔍 驗證導入結果...")

        # 驗證 Neo4j
        with self.neo4j_driver.session() as session:
            result = session.run("MATCH (a:Artwork) RETURN count(a) as count")
            neo4j_count = result.single()['count']
            logger.info(f"   Neo4j 藝術品數量: {neo4j_count}")

            result = session.run("MATCH (a:Artist) RETURN count(a) as count")
            artist_count = result.single()['count']
            logger.info(f"   Neo4j 藝術家數量: {artist_count}")

        # 驗證 ChromaDB
        chroma_count = self.collection.count()
        logger.info(f"   ChromaDB 向量數量: {chroma_count}")

        # 測試查詢
        logger.info("\n🧪 測試查詢:")

        # 測試 ChromaDB 查詢
        try:
            results = self.collection.query(
                query_texts=["impressionist painting"],
                n_results=3
            )
            logger.info(f"   ChromaDB 查詢 'impressionist painting': {len(results['ids'][0])} 個結果")
            for i, (id, doc, meta) in enumerate(zip(results['ids'][0], results['documents'][0], results['metadatas'][0])):
                logger.info(f"      {i+1}. {meta.get('title', 'N/A')} by {meta.get('artist', 'N/A')}")
        except Exception as e:
            logger.warning(f"   ChromaDB 查詢測試失敗: {e}")


def main():
    """主函數"""
    logger.info("=" * 60)
    logger.info("🎨 藝術史資料導入工具")
    logger.info("=" * 60)

    # 創建導入器
    importer = ArtDataImporter()

    try:
        # 載入資料
        artworks = importer.load_json_files()

        if not artworks:
            logger.error("❌ 沒有找到可導入的資料")
            return

        # 導入到 Neo4j
        neo4j_count = importer.import_to_neo4j(artworks)

        # 導入到 ChromaDB
        chromadb_count = importer.import_to_chromadb(artworks)

        # 驗證導入
        importer.verify_import()

        logger.info("\n" + "=" * 60)
        logger.info("🎉 資料導入完成！")
        logger.info(f"   Neo4j: {neo4j_count} 件作品")
        logger.info(f"   ChromaDB: {chromadb_count} 個向量")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"❌ 導入過程發生錯誤: {e}")
        import traceback
        traceback.print_exc()

    finally:
        importer.close()


if __name__ == "__main__":
    main()
