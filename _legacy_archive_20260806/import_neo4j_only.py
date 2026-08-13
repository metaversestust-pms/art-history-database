#!/usr/bin/env python3
"""
簡化的Neo4j匯入腳本 - 只需要neo4j套件
"""

import json
import logging
import sys
from pathlib import Path
from typing import List, Dict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from neo4j import GraphDatabase
except ImportError as e:
    logger.error(f"缺少neo4j套件: {e}")
    logger.info("請安裝: pip install neo4j")
    sys.exit(1)


class Neo4jOnlyImporter:
    """只匯入到Neo4j"""

    def __init__(self, data_dir="./comprehensive_art_data"):
        self.data_dir = Path(data_dir)

        # Neo4j 配置
        self.neo4j_uri = "bolt://localhost:7687"
        self.neo4j_user = "neo4j"
        self.neo4j_password = "arthistory123"

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

    def import_all_periods(self):
        """匯入所有時期的資料"""
        logger.info("🚀 開始匯入綜合藝術史資料到Neo4j")
        logger.info("="*60)

        # 連接Neo4j
        neo4j_driver = self.connect_neo4j()

        if not neo4j_driver:
            logger.error("❌ 無法連接Neo4j，請確認Docker容器運行中")
            return

        # 查找所有時期的資料檔案
        period_files = list(self.data_dir.glob("*_artworks.json"))

        if not period_files:
            logger.error(f"❌ 在 {self.data_dir} 找不到資料檔案")
            logger.info("請先運行: python3 comprehensive_art_history_crawler.py")
            return

        logger.info(f"找到 {len(period_files)} 個時期的資料檔案")

        total_imported = 0

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
            total_imported += neo4j_count

        # 關閉連接
        neo4j_driver.close()

        # 生成總結報告
        logger.info(f"\n{'='*60}")
        logger.info("📊 匯入總結")
        logger.info(f"{'='*60}")
        logger.info(f"Neo4j 匯入: {total_imported} 件")
        logger.info(f"{'='*60}")

        logger.info("\n✅ 資料匯入完成！")
        logger.info("\n💡 下一步:")
        logger.info("1. 在OpenWebUI測試新資料: http://localhost:8080")
        logger.info("2. 使用系統狀態檢查: bash check_system_status.sh")


def main():
    print("\n🎨 Neo4j資料匯入工具")
    print("="*60)

    data_dir = input("資料目錄（按Enter使用默認: ./comprehensive_art_data）: ").strip()
    if not data_dir:
        data_dir = "./comprehensive_art_data"

    confirm = input(f"\n確認開始匯入到Neo4j？(y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ 已取消")
        return

    importer = Neo4jOnlyImporter(data_dir=data_dir)
    importer.import_all_periods()

    print("\n✅ 匯入完成！")


if __name__ == "____main__":
    main()
