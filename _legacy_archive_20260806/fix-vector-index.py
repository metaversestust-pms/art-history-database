#!/usr/bin/env python3
"""
修復向量索引維度
"""

from neo4j import GraphDatabase
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_vector_indexes():
    """刪除並重建向量索引為 512 維"""

    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "arthistory123"))

    with driver.session() as session:
        logger.info("🔧 刪除舊的向量索引...")

        # 刪除舊索引
        indexes_to_drop = ['artist_name_embeddings', 'artwork_title_embeddings', 'movement_embeddings']

        for idx_name in indexes_to_drop:
            try:
                session.run(f"DROP INDEX {idx_name} IF EXISTS")
                logger.info(f"  ✅ 刪除: {idx_name}")
            except Exception as e:
                logger.warning(f"  ⚠️  {idx_name}: {e}")

        logger.info("\n🔧 創建新的 512 維向量索引...")

        # 創建新索引（512維）
        new_indexes = [
            {
                'name': 'artist_name_embeddings',
                'label': 'Artist',
                'property': 'name_embedding',
                'dimensions': 512
            },
            {
                'name': 'artwork_title_embeddings',
                'label': 'Artwork',
                'property': 'title_embedding',
                'dimensions': 512
            },
            {
                'name': 'movement_embeddings',
                'label': 'Movement',
                'property': 'description_embedding',
                'dimensions': 512
            }
        ]

        for idx in new_indexes:
            try:
                query = f"""
                CREATE VECTOR INDEX {idx['name']} IF NOT EXISTS
                FOR (n:{idx['label']})
                ON (n.{idx['property']})
                OPTIONS {{
                    indexConfig: {{
                        `vector.dimensions`: {idx['dimensions']},
                        `vector.similarity_function`: 'cosine'
                    }}
                }}
                """
                session.run(query)
                logger.info(f"  ✅ 創建: {idx['name']} ({idx['dimensions']}維)")
            except Exception as e:
                logger.error(f"  ❌ {idx['name']}: {e}")

    driver.close()
    logger.info("\n✅ 索引修復完成")

if __name__ == "__main__":
    fix_vector_indexes()
