#!/usr/bin/env python3
"""
簡化版藝術史資料導入腳本
"""

import json
import os
import logging
from neo4j import GraphDatabase
import chromadb

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 使用 Docker 網路中的容器名稱
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://art-history-neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "arthistory123")
CHROMADB_HOST = os.getenv("CHROMADB_HOST", "art-history-chromadb")
CHROMADB_PORT = int(os.getenv("CHROMADB_PORT", "8000"))

def load_artworks(data_dir="/app/data/raw"):
    """載入所有藝術品資料"""
    artworks = []
    for filename in os.listdir(data_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(data_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        artworks.extend(data)
                        logger.info(f"✅ 載入 {filename}: {len(data)} 件")
            except Exception as e:
                logger.warning(f"⚠️ 跳過 {filename}: {e}")

    logger.info(f"📊 總共: {len(artworks)} 件藝術品")
    return artworks

def import_to_neo4j(artworks):
    """導入到 Neo4j"""
    logger.info(f"🔄 連接 Neo4j: {NEO4J_URI}")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    with driver.session() as session:
        # 創建約束
        try:
            session.run("CREATE CONSTRAINT artwork_id IF NOT EXISTS FOR (a:Artwork) REQUIRE a.id IS UNIQUE")
        except:
            pass

        # 導入資料
        count = 0
        for artwork in artworks:
            try:
                session.run("""
                    MERGE (a:Artwork {id: $id})
                    SET a.title = $title,
                        a.artist = $artist,
                        a.date = $date,
                        a.medium = $medium,
                        a.source = $source

                    MERGE (artist:Artist {name: $artist})
                    MERGE (artist)-[:CREATED]->(a)
                """,
                    id=str(artwork.get('id', f'art_{count}')),
                    title=artwork.get('title', 'Unknown'),
                    artist=artwork.get('artist', 'Unknown'),
                    date=artwork.get('date', ''),
                    medium=artwork.get('medium', ''),
                    source=artwork.get('source', 'Unknown')
                )
                count += 1
                if count % 100 == 0:
                    logger.info(f"   已導入 {count} 件...")
            except Exception as e:
                logger.warning(f"⚠️ 跳過作品: {e}")

    driver.close()
    logger.info(f"✅ Neo4j: {count} 件作品")
    return count

def import_to_chromadb(artworks):
    """導入到 ChromaDB"""
    logger.info(f"🔄 連接 ChromaDB: {CHROMADB_HOST}:{CHROMADB_PORT}")

    client = chromadb.HttpClient(host=CHROMADB_HOST, port=CHROMADB_PORT)
    collection = client.get_or_create_collection(name="art_history")

    # 批量導入
    ids = []
    documents = []
    metadatas = []

    for i, artwork in enumerate(artworks):
        artwork_id = str(artwork.get('id', f'art_{i}'))

        # 創建文本描述
        parts = []
        if artwork.get('title'):
            parts.append(f"標題: {artwork['title']}")
        if artwork.get('artist'):
            parts.append(f"藝術家: {artwork['artist']}")
        if artwork.get('date'):
            parts.append(f"時間: {artwork['date']}")
        if artwork.get('medium'):
            parts.append(f"媒材: {artwork['medium']}")

        text = " | ".join(parts)

        # 元數據
        metadata = {
            'title': artwork.get('title', 'Unknown')[:500],
            'artist': artwork.get('artist', 'Unknown')[:500],
            'date': artwork.get('date', '')[:100],
            'source': artwork.get('source', 'Unknown')[:100]
        }

        ids.append(artwork_id)
        documents.append(text)
        metadatas.append(metadata)

    # 批量添加
    batch_size = 100
    count = 0
    for i in range(0, len(ids), batch_size):
        try:
            collection.add(
                ids=ids[i:i+batch_size],
                documents=documents[i:i+batch_size],
                metadatas=metadatas[i:i+batch_size]
            )
            count += len(ids[i:i+batch_size])
            logger.info(f"   已導入 {count} 件...")
        except Exception as e:
            logger.warning(f"⚠️ 批次失敗: {e}")

    logger.info(f"✅ ChromaDB: {count} 個向量")
    return count

def main():
    logger.info("=" * 60)
    logger.info("🎨 藝術史資料導入")
    logger.info("=" * 60)

    # 載入資料
    artworks = load_artworks()

    if not artworks:
        logger.error("❌ 沒有資料")
        return

    # 導入
    neo4j_count = import_to_neo4j(artworks)
    chromadb_count = import_to_chromadb(artworks)

    logger.info("=" * 60)
    logger.info(f"🎉 完成！Neo4j: {neo4j_count}, ChromaDB: {chromadb_count}")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
