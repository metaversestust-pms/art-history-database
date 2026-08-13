#!/usr/bin/env python3
"""
將新收集的藝術史資料更新到Neo4j知識圖譜
"""

import json
import os
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Set
import re

try:
    from neo4j import GraphDatabase
    from neo4j.exceptions import ServiceUnavailable, AuthError
except ImportError:
    print("❌ 請安裝neo4j驅動: pip install neo4j")
    exit(1)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Neo4jArtDataUpdater:
    def __init__(self):
        self.neo4j_uri = "bolt://localhost:7687"
        self.neo4j_user = "neo4j"
        self.neo4j_password = "arthistory123"
        self.driver = None

        # 統計
        self.stats = {
            'artworks_added': 0,
            'artists_added': 0,
            'cultures_added': 0,
            'movements_added': 0,
            'museums_added': 0,
            'relationships_added': 0,
            'errors': 0,
            'duplicates_skipped': 0
        }

        # 防重複集合
        self.existing_entities = {
            'artworks': set(),
            'artists': set(),
            'cultures': set(),
            'movements': set(),
            'museums': set()
        }

    def connect_to_neo4j(self):
        """連接到Neo4j數據庫"""
        try:
            self.driver = GraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_user, self.neo4j_password)
            )

            # 測試連接
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                test_value = result.single()["test"]
                if test_value == 1:
                    logger.info("✅ Neo4j連接成功")
                    return True

        except ServiceUnavailable:
            logger.error("❌ Neo4j服務不可用，請確認Neo4j正在運行")
            return False
        except AuthError:
            logger.error("❌ Neo4j認證失敗，請檢查用戶名和密碼")
            return False
        except Exception as e:
            logger.error(f"❌ Neo4j連接失敗: {e}")
            return False

    def load_existing_entities(self):
        """載入現有實體以避免重複"""
        try:
            with self.driver.session() as session:
                # 載入現有藝術品
                result = session.run("MATCH (a:Artwork) RETURN a.id as id")
                self.existing_entities['artworks'] = {record["id"] for record in result if record["id"]}

                # 載入現有藝術家
                result = session.run("MATCH (a:Artist) RETURN a.name as name")
                self.existing_entities['artists'] = {record["name"] for record in result if record["name"]}

                # 載入現有文化
                result = session.run("MATCH (c:Culture) RETURN c.name as name")
                self.existing_entities['cultures'] = {record["name"] for record in result if record["name"]}

                # 載入現有流派
                result = session.run("MATCH (m:Movement) RETURN m.name as name")
                self.existing_entities['movements'] = {record["name"] for record in result if record["name"]}

                # 載入現有博物館
                result = session.run("MATCH (m:Museum) RETURN m.name as name")
                self.existing_entities['museums'] = {record["name"] for record in result if record["name"]}

                logger.info(f"📊 載入現有實體: 藝術品{len(self.existing_entities['artworks'])}, "
                          f"藝術家{len(self.existing_entities['artists'])}, "
                          f"文化{len(self.existing_entities['cultures'])}")

        except Exception as e:
            logger.error(f"❌ 載入現有實體失敗: {e}")

    def normalize_name(self, name: str) -> str:
        """標準化名稱"""
        if not name or name in ['未知', '未知藝術家', '未知標題', 'Unknown', 'unknown']:
            return None

        # 清理名稱
        name = str(name).strip()
        # 移除多餘空格
        name = re.sub(r'\s+', ' ', name)
        # 移除特殊字符
        name = re.sub(r'[^\w\s\-\.\'\"]+', '', name, flags=re.UNICODE)

        return name if len(name) > 1 else None

    def extract_year_from_date(self, date_str: str) -> int:
        """從日期字符串中提取年份"""
        if not date_str:
            return None

        # 查找4位數年份
        year_match = re.search(r'\b(1[0-9]{3}|20[0-9]{2})\b', str(date_str))
        if year_match:
            return int(year_match.group(1))

        return None

    def determine_movement(self, item: Dict) -> str:
        """根據作品信息推斷藝術流派"""
        title = str(item.get('title', '')).lower()
        artist = str(item.get('artist', '')).lower()
        date = str(item.get('date', '')).lower()
        medium = str(item.get('medium', '')).lower()
        description = str(item.get('description', '')).lower()

        # 組合所有文本進行分析
        text = f"{title} {artist} {date} {medium} {description}"

        # 流派關鍵詞映射
        movements = {
            'Renaissance': ['renaissance', 'leonardo', 'michelangelo', 'raphael', 'botticelli'],
            'Baroque': ['baroque', 'caravaggio', 'rubens', 'rembrandt', 'bernini'],
            'Impressionism': ['impressionist', 'monet', 'renoir', 'degas', 'manet'],
            'Post-Impressionism': ['post-impressionist', 'van gogh', 'cezanne', 'gauguin'],
            'Cubism': ['cubist', 'picasso', 'braque', 'cubism'],
            'Surrealism': ['surreal', 'dali', 'magritte', 'ernst'],
            'Abstract': ['abstract', 'kandinsky', 'mondrian', 'pollock'],
            'Contemporary': ['contemporary', 'modern', 'installation', 'video art'],
            'Asian Art': ['chinese', 'japanese', 'korean', 'asian', 'ukiyo-e', 'calligraphy'],
            'Islamic Art': ['islamic', 'persian', 'arabic', 'calligraphy', 'mosque'],
            'Medieval': ['medieval', 'gothic', 'romanesque', 'byzantine'],
            'Classical': ['classical', 'ancient', 'greek', 'roman']
        }

        for movement, keywords in movements.items():
            if any(keyword in text for keyword in keywords):
                return movement

        return None

    def create_artwork_node(self, session, item: Dict) -> bool:
        """創建藝術品節點"""
        try:
            artwork_id = f"artwork_{item.get('id', '')}"
            if artwork_id in self.existing_entities['artworks']:
                self.stats['duplicates_skipped'] += 1
                return False

            title = self.normalize_name(item.get('title'))
            if not title:
                return False

            # 提取年份
            creation_year = self.extract_year_from_date(item.get('date', ''))

            # 推斷流派
            movement = self.determine_movement(item)

            query = """
            CREATE (a:Artwork {
                id: $id,
                title: $title,
                medium: $medium,
                date_created: $date_created,
                creation_year: $creation_year,
                description: $description,
                source: $source,
                source_url: $source_url,
                image_url: $image_url,
                rights: $rights,
                movement: $movement,
                created_at: datetime()
            })
            """

            session.run(query, {
                'id': artwork_id,
                'title': title,
                'medium': self.normalize_name(item.get('medium', '')),
                'date_created': item.get('date', ''),
                'creation_year': creation_year,
                'description': item.get('description', ''),
                'source': item.get('source', ''),
                'source_url': item.get('source_url', ''),
                'image_url': item.get('image_url', ''),
                'rights': item.get('rights', ''),
                'movement': movement
            })

            self.existing_entities['artworks'].add(artwork_id)
            self.stats['artworks_added'] += 1
            return True

        except Exception as e:
            logger.error(f"❌ 創建藝術品節點失敗: {e}")
            self.stats['errors'] += 1
            return False

    def create_artist_node(self, session, artist_name: str) -> bool:
        """創建藝術家節點"""
        try:
            artist_name = self.normalize_name(artist_name)
            if not artist_name or artist_name in self.existing_entities['artists']:
                return False

            query = """
            MERGE (a:Artist {name: $name})
            ON CREATE SET a.created_at = datetime()
            """

            session.run(query, {'name': artist_name})
            self.existing_entities['artists'].add(artist_name)
            self.stats['artists_added'] += 1
            return True

        except Exception as e:
            logger.error(f"❌ 創建藝術家節點失敗: {e}")
            self.stats['errors'] += 1
            return False

    def create_culture_node(self, session, culture_name: str) -> bool:
        """創建文化節點"""
        try:
            culture_name = self.normalize_name(culture_name)
            if not culture_name or culture_name in self.existing_entities['cultures']:
                return False

            query = """
            MERGE (c:Culture {name: $name})
            ON CREATE SET c.created_at = datetime()
            """

            session.run(query, {'name': culture_name})
            self.existing_entities['cultures'].add(culture_name)
            self.stats['cultures_added'] += 1
            return True

        except Exception as e:
            logger.error(f"❌ 創建文化節點失敗: {e}")
            self.stats['errors'] += 1
            return False

    def create_movement_node(self, session, movement_name: str) -> bool:
        """創建藝術流派節點"""
        try:
            if not movement_name or movement_name in self.existing_entities['movements']:
                return False

            query = """
            MERGE (m:Movement {name: $name})
            ON CREATE SET m.created_at = datetime()
            """

            session.run(query, {'name': movement_name})
            self.existing_entities['movements'].add(movement_name)
            self.stats['movements_added'] += 1
            return True

        except Exception as e:
            logger.error(f"❌ 創建流派節點失敗: {e}")
            self.stats['errors'] += 1
            return False

    def create_museum_node(self, session, museum_name: str) -> bool:
        """創建博物館節點"""
        try:
            museum_name = self.normalize_name(museum_name)
            if not museum_name or museum_name in self.existing_entities['museums']:
                return False

            query = """
            MERGE (m:Museum {name: $name})
            ON CREATE SET m.created_at = datetime()
            """

            session.run(query, {'name': museum_name})
            self.existing_entities['museums'].add(museum_name)
            self.stats['museums_added'] += 1
            return True

        except Exception as e:
            logger.error(f"❌ 創建博物館節點失敗: {e}")
            self.stats['errors'] += 1
            return False

    def create_relationships(self, session, item: Dict):
        """創建關係"""
        try:
            artwork_id = f"artwork_{item.get('id', '')}"

            # 藝術家創作關係
            artist_name = self.normalize_name(item.get('artist'))
            if artist_name and artist_name in self.existing_entities['artists']:
                query = """
                MATCH (artist:Artist {name: $artist_name})
                MATCH (artwork:Artwork {id: $artwork_id})
                MERGE (artist)-[:CREATED]->(artwork)
                """
                session.run(query, {'artist_name': artist_name, 'artwork_id': artwork_id})
                self.stats['relationships_added'] += 1

            # 文化歸屬關係
            culture_name = self.normalize_name(item.get('culture'))
            if culture_name and culture_name in self.existing_entities['cultures']:
                query = """
                MATCH (culture:Culture {name: $culture_name})
                MATCH (artwork:Artwork {id: $artwork_id})
                MERGE (artwork)-[:BELONGS_TO]->(culture)
                """
                session.run(query, {'culture_name': culture_name, 'artwork_id': artwork_id})
                self.stats['relationships_added'] += 1

            # 流派歸屬關係
            movement = self.determine_movement(item)
            if movement and movement in self.existing_entities['movements']:
                query = """
                MATCH (movement:Movement {name: $movement_name})
                MATCH (artwork:Artwork {id: $artwork_id})
                MERGE (artwork)-[:BELONGS_TO_MOVEMENT]->(movement)
                """
                session.run(query, {'movement_name': movement, 'artwork_id': artwork_id})
                self.stats['relationships_added'] += 1

            # 博物館收藏關係
            provider = self.normalize_name(item.get('provider'))
            if provider and provider in self.existing_entities['museums']:
                query = """
                MATCH (museum:Museum {name: $museum_name})
                MATCH (artwork:Artwork {id: $artwork_id})
                MERGE (museum)-[:HOUSES]->(artwork)
                """
                session.run(query, {'museum_name': provider, 'artwork_id': artwork_id})
                self.stats['relationships_added'] += 1

        except Exception as e:
            logger.error(f"❌ 創建關係失敗: {e}")
            self.stats['errors'] += 1

    def process_data_file(self, file_path: Path):
        """處理單個數據文件"""
        try:
            logger.info(f"📁 處理文件: {file_path.name}")

            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 提取項目
            items = []
            if 'items' in data:
                items = data['items']
            elif isinstance(data, list):
                items = data

            logger.info(f"📊 文件包含 {len(items)} 項藝術資料")

            processed = 0
            with self.driver.session() as session:
                for item in items:
                    # 創建實體
                    artwork_created = self.create_artwork_node(session, item)

                    if artwork_created:
                        # 創建相關實體
                        artist_name = self.normalize_name(item.get('artist'))
                        if artist_name:
                            self.create_artist_node(session, artist_name)

                        culture_name = self.normalize_name(item.get('culture'))
                        if culture_name:
                            self.create_culture_node(session, culture_name)

                        movement = self.determine_movement(item)
                        if movement:
                            self.create_movement_node(session, movement)

                        provider = self.normalize_name(item.get('provider'))
                        if provider:
                            self.create_museum_node(session, provider)

                        # 創建關係
                        self.create_relationships(session, item)

                        processed += 1

                    # 批量提交
                    if processed % 100 == 0:
                        logger.info(f"   ✅ 已處理 {processed} 項")

            logger.info(f"✅ 文件 {file_path.name} 處理完成，處理 {processed} 項")

        except Exception as e:
            logger.error(f"❌ 處理文件 {file_path.name} 失敗: {e}")
            self.stats['errors'] += 1

    def update_neo4j_with_new_data(self):
        """將新資料更新到Neo4j"""
        logger.info("🚀 開始更新Neo4j知識圖譜...")

        # 連接Neo4j
        if not self.connect_to_neo4j():
            return False

        # 載入現有實體
        self.load_existing_entities()

        # 獲取新數據文件
        raw_data_dir = Path('./data/raw')
        new_files = [
            'specialized_art_2025-09-27T12-45-37.210Z.json',
            'specialized_art_2025-09-27T12-45-10.779Z.json',
            'specialized_art_2025-09-27T12-44-44.138Z.json',
            'met_museum_crawled_2025-09-26T07-23-53-045Z.json',
            'google_books_art_2025-09-26T01-25-41-025Z.json'
        ]

        # 處理每個文件
        for filename in new_files:
            file_path = raw_data_dir / filename
            if file_path.exists():
                self.process_data_file(file_path)
            else:
                logger.warning(f"⚠️ 文件不存在: {filename}")

        # 關閉連接
        if self.driver:
            self.driver.close()

        # 打印總結
        self.print_summary()
        return True

    def print_summary(self):
        """打印更新總結"""
        logger.info(f"\n🎉 Neo4j知識圖譜更新完成！")
        logger.info(f"📊 更新統計:")
        logger.info(f"   - 新增藝術品: {self.stats['artworks_added']}")
        logger.info(f"   - 新增藝術家: {self.stats['artists_added']}")
        logger.info(f"   - 新增文化: {self.stats['cultures_added']}")
        logger.info(f"   - 新增流派: {self.stats['movements_added']}")
        logger.info(f"   - 新增博物館: {self.stats['museums_added']}")
        logger.info(f"   - 新增關係: {self.stats['relationships_added']}")
        logger.info(f"   - 跳過重複: {self.stats['duplicates_skipped']}")
        logger.info(f"   - 錯誤數量: {self.stats['errors']}")

def main():
    """主程序"""
    try:
        updater = Neo4jArtDataUpdater()
        success = updater.update_neo4j_with_new_data()
        return 0 if success else 1
    except Exception as e:
        logger.error(f"❌ 程序執行失敗: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())