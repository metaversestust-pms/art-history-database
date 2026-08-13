#!/usr/bin/env python3
"""
將新古典主義和浪漫主義資料匯入 Neo4j 和 ChromaDB
"""

import json
import logging
from pathlib import Path
from neo4j import GraphDatabase
import requests

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Neo4j 連接配置
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "arthistory123"

class Neo4jImporter:
    """Neo4j 資料匯入器"""

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def import_artwork(self, artwork_data):
        """匯入藝術品到 Neo4j"""
        with self.driver.session() as session:
            return session.execute_write(self._create_artwork, artwork_data)

    @staticmethod
    def _create_artwork(tx, data):
        """創建藝術品節點和關係"""
        # 提取基本資訊
        artwork_id = data.get('id') or data.get('objectid')
        title = data.get('title', 'Untitled')
        description = data.get('description', '')
        dated = data.get('dated', '')
        period = data.get('period', '')
        culture = data.get('culture', '')
        classification = data.get('classification', '')

        # 創建 Artwork 節點
        query = """
        MERGE (a:Artwork {id: $artwork_id})
        SET a.title = $title,
            a.description = $description,
            a.dated = $dated,
            a.period = $period,
            a.culture = $culture,
            a.classification = $classification,
            a.source = 'Harvard Art Museums',
            a.art_period = 'Neoclassical/Romantic'
        RETURN a
        """

        result = tx.run(query,
                       artwork_id=str(artwork_id),
                       title=title,
                       description=description,
                       dated=dated,
                       period=period,
                       culture=culture,
                       classification=classification)

        # 創建藝術家關係
        people = data.get('people', [])
        for person in people:
            person_name = person.get('name') or person.get('displayname')
            if person_name:
                person_query = """
                MERGE (p:Person {name: $name})
                WITH p
                MATCH (a:Artwork {id: $artwork_id})
                MERGE (p)-[:CREATED]->(a)
                """
                tx.run(person_query, name=person_name, artwork_id=str(artwork_id))

        # 創建時期關係
        if period:
            period_query = """
            MERGE (per:Period {name: $period})
            WITH per
            MATCH (a:Artwork {id: $artwork_id})
            MERGE (a)-[:BELONGS_TO_PERIOD]->(per)
            """
            tx.run(period_query, period=period, artwork_id=str(artwork_id))

        return result.single()

def import_to_neo4j(json_file):
    """將 JSON 資料匯入 Neo4j"""
    logger.info(f"\n🚀 開始匯入資料到 Neo4j...")
    logger.info(f"📁 資料檔案: {json_file}")

    # 讀取 JSON 資料
    with open(json_file, 'r', encoding='utf-8') as f:
        artworks = json.load(f)

    logger.info(f"📦 共有 {len(artworks)} 件藝術品待匯入")

    # 創建匯入器
    importer = Neo4jImporter(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    success_count = 0
    error_count = 0

    try:
        for i, artwork in enumerate(artworks, 1):
            try:
                importer.import_artwork(artwork)
                success_count += 1
                if i % 10 == 0:
                    logger.info(f"   ✅ 已匯入 {i}/{len(artworks)} 件作品")
            except Exception as e:
                error_count += 1
                logger.error(f"   ❌ 匯入失敗 (ID: {artwork.get('id')}): {e}")

    finally:
        importer.close()

    logger.info(f"\n✅ Neo4j 匯入完成!")
    logger.info(f"   成功: {success_count} 件")
    logger.info(f"   失敗: {error_count} 件")

    return success_count, error_count

def verify_neo4j_import():
    """驗證 Neo4j 匯入結果"""
    logger.info(f"\n🔍 驗證 Neo4j 匯入結果...")

    try:
        response = requests.post(
            "http://localhost:7474/db/neo4j/tx/commit",
            auth=("neo4j", "arthistory123"),
            json={
                "statements": [{
                    "statement": """
                    MATCH (a:Artwork)
                    WHERE a.art_period = 'Neoclassical/Romantic'
                    RETURN count(a) as count
                    """
                }]
            },
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            count = result["results"][0]["data"][0]["row"][0]
            logger.info(f"   ✅ 找到 {count} 件新古典/浪漫主義作品")
            return count
        else:
            logger.error(f"   ❌ 驗證失敗: HTTP {response.status_code}")
            return 0

    except Exception as e:
        logger.error(f"   ❌ 驗證錯誤: {e}")
        return 0

def main():
    """主函數"""
    print("\n" + "="*70)
    print("🎨 新古典主義與浪漫主義資料匯入系統")
    print("="*70)

    # 尋找最新的 JSON 檔案
    data_dir = Path("./comprehensive_art_data/neoclassical_romantic")
    json_files = sorted(data_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)

    if not json_files:
        logger.error("❌ 找不到資料檔案！")
        return

    json_file = json_files[0]
    logger.info(f"📁 使用資料檔案: {json_file}")

    # 匯入到 Neo4j
    success, errors = import_to_neo4j(json_file)

    # 驗證匯入
    count = verify_neo4j_import()

    # 總結
    print("\n" + "="*70)
    print("📊 匯入總結")
    print("="*70)
    print(f"Neo4j 匯入成功: {success} 件")
    print(f"Neo4j 匯入失敗: {errors} 件")
    print(f"Neo4j 驗證結果: {count} 件作品")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
