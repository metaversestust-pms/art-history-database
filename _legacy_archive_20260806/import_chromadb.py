#!/usr/bin/env python3
"""
ChromaDB 資料導入（支援 v2 API）
"""

import json
import os
import logging
from neo4j import GraphDatabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 使用 Docker 網路中的容器名稱
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://art-history-neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "arthistory123")

def get_artworks_from_neo4j():
    """從 Neo4j 獲取所有藝術品"""
    logger.info(f"🔄 從 Neo4j 載入資料...")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    artworks = []
    with driver.session() as session:
        result = session.run("""
            MATCH (a:Artwork)
            RETURN a.id as id, a.title as title, a.artist as artist,
                   a.date as date, a.medium as medium, a.source as source,
                   a.description as description, a.period as period
        """)

        for record in result:
            artworks.append({
                'id': record['id'],
                'title': record['title'],
                'artist': record['artist'],
                'date': record['date'],
                'medium': record['medium'],
                'source': record['source'],
                'description': record['description'],
                'period': record['period']
            })

    driver.close()
    logger.info(f"✅ 獲取 {len(artworks)} 件藝術品")
    return artworks

def import_to_chromadb_v2(artworks):
    """使用 ChromaDB Python 客戶端導入"""
    import chromadb

    CHROMADB_HOST = os.getenv("CHROMADB_HOST", "art-history-chromadb")
    CHROMADB_PORT = int(os.getenv("CHROMADB_PORT", "8000"))

    logger.info(f"🔄 連接到 ChromaDB: {CHROMADB_HOST}:{CHROMADB_PORT}")

    # 使用 Python 客戶端
    client = chromadb.HttpClient(host=CHROMADB_HOST, port=CHROMADB_PORT)

    # 創建或獲取 collection
    collection_name = "art_history"

    try:
        collection = client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "藝術史知識庫"}
        )
        logger.info(f"✅ Collection: {collection_name}")
    except Exception as e:
        logger.error(f"❌ 無法創建 collection: {e}")
        return 0

    # 準備資料
    ids = []
    documents = []
    metadatas = []

    for artwork in artworks:
        if not artwork.get('id'):
            continue

        # 創建文本描述（使用英文關鍵字以便更好的檢索）
        parts = []
        if artwork.get('title'):
            parts.append(f"Title: {artwork['title']}")
        if artwork.get('artist'):
            parts.append(f"Artist: {artwork['artist']}")
        if artwork.get('date'):
            parts.append(f"Date: {artwork['date']}")
        if artwork.get('period'):
            parts.append(f"Period: {artwork['period']}")
        if artwork.get('medium'):
            parts.append(f"Medium: {artwork['medium']}")
        if artwork.get('description'):
            parts.append(f"Description: {artwork['description']}")

        text = " | ".join(parts)

        if not text:
            continue

        # 元數據
        metadata = {
            'title': str(artwork.get('title', 'Unknown'))[:500],
            'artist': str(artwork.get('artist', 'Unknown'))[:500],
            'date': str(artwork.get('date', ''))[:100],
            'source': str(artwork.get('source', 'Unknown'))[:100]
        }

        ids.append(str(artwork.get('id', '')))
        documents.append(text)
        metadatas.append(metadata)

    # 批量添加
    batch_size = 100
    count = 0

    for i in range(0, len(ids), batch_size):
        batch_ids = ids[i:i+batch_size]
        batch_docs = documents[i:i+batch_size]
        batch_metas = metadatas[i:i+batch_size]

        try:
            collection.add(
                ids=batch_ids,
                documents=batch_docs,
                metadatas=batch_metas
            )
            count += len(batch_ids)
            logger.info(f"   已導入 {count}/{len(ids)} 件...")

        except Exception as e:
            logger.warning(f"⚠️ 批次失敗: {e}")

    logger.info(f"✅ ChromaDB: {count} 個向量")
    return count

def main():
    logger.info("=" * 60)
    logger.info("🎨 ChromaDB 資料導入")
    logger.info("=" * 60)

    # 從 Neo4j 獲取資料
    artworks = get_artworks_from_neo4j()

    if not artworks:
        logger.error("❌ 沒有資料")
        return

    # 導入到 ChromaDB
    chromadb_count = import_to_chromadb_v2(artworks)

    logger.info("=" * 60)
    logger.info(f"🎉 完成！ChromaDB: {chromadb_count} 個向量")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
