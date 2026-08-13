#!/usr/bin/env python3
"""
將爬蟲收集的藝術史數據導入到Neo4j知識圖譜
處理所有數據源：Europeana、Met Museum、Google Books等
"""

import json
import os
import logging
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from neo4j import GraphDatabase
import uuid
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ProcessedEntity:
    """處理後的實體"""
    entity_type: str
    name: str
    properties: Dict[str, Any]
    source_data: Dict[str, Any]

class CrawlerDataProcessor:
    """爬蟲數據處理器"""

    def __init__(self, neo4j_url: str = "bolt://localhost:7687",
                 username: str = "neo4j", password: str = "arthistory123"):
        self.neo4j_url = neo4j_url
        self.username = username
        self.password = password
        self.driver = None

    def connect_neo4j(self):
        """連接Neo4j"""
        try:
            self.driver = GraphDatabase.driver(self.neo4j_url, auth=(self.username, self.password))
            with self.driver.session() as session:
                session.run("RETURN 1")
            logger.info("✅ Neo4j連接成功")
            return True
        except Exception as e:
            logger.error(f"❌ Neo4j連接失敗: {e}")
            return False

    def process_all_crawler_data(self):
        """處理所有爬蟲數據"""
        if not self.connect_neo4j():
            return False

        data_dir = "./data/raw"
        if not os.path.exists(data_dir):
            logger.error(f"❌ 數據目錄不存在: {data_dir}")
            return False

        total_processed = 0

        # 處理所有JSON文件
        for filename in os.listdir(data_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(data_dir, filename)
                logger.info(f"🔄 處理文件: {filename}")

                try:
                    processed_count = self.process_data_file(file_path)
                    total_processed += processed_count
                    logger.info(f"✅ {filename}: 處理了 {processed_count} 項數據")
                except Exception as e:
                    logger.error(f"❌ 處理文件失敗 {filename}: {e}")

        logger.info(f"🎉 總共處理了 {total_processed} 項數據到Neo4j")
        self.driver.close()
        return True

    def process_data_file(self, file_path: str) -> int:
        """處理單個數據文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        processed_count = 0

        # 根據文件名識別數據源
        filename = os.path.basename(file_path).lower()

        if 'europeana' in filename:
            processed_count = self.process_europeana_data(data)
        elif 'met_museum' in filename:
            processed_count = self.process_met_data(data)
        elif 'google_books' in filename:
            processed_count = self.process_books_data(data)
        elif 'renaissance_baroque' in filename:
            processed_count = self.process_met_data(data)  # 同樣的Met Museum格式
        else:
            logger.warning(f"⚠️ 未知數據格式: {filename}")

        return processed_count

    def process_europeana_data(self, data: Dict) -> int:
        """處理Europeana數據"""
        if 'data' not in data:
            return 0

        items = data['data']
        processed_count = 0

        with self.driver.session() as session:
            for item in items:
                try:
                    # 創建藝術作品節點
                    artwork_properties = {
                        'europeana_id': item.get('europeanaId', ''),
                        'title': self.clean_text(item.get('title', 'Unknown')),
                        'date': item.get('date', ''),
                        'type': item.get('type', ''),
                        'description': self.clean_text(item.get('description', '')),
                        'country': item.get('country', ''),
                        'language': item.get('language', ''),
                        'thumbnail': item.get('thumbnail', ''),
                        'url': item.get('europeanaUrl', ''),
                        'completeness': item.get('completeness', 0),
                        'source': 'Europeana',
                        'created_at': datetime.now().isoformat(),
                        'data_quality_score': item.get('qualityScore', 0)
                    }

                    # 創建藝術作品
                    session.run("""
                        MERGE (artwork:Artwork {europeana_id: $europeana_id})
                        SET artwork += $props
                        """,
                        europeana_id=artwork_properties['europeana_id'],
                        props=artwork_properties
                    )

                    # 處理創作者
                    creators = item.get('creator', [])
                    if isinstance(creators, str):
                        creators = [creators]

                    for creator_name in creators:
                        if creator_name and creator_name.strip():
                            creator_name = self.clean_text(creator_name)

                            # 創建藝術家
                            session.run("""
                                MERGE (artist:Artist {name: $name})
                                SET artist.source = 'Europeana',
                                    artist.created_at = $created_at
                                """,
                                name=creator_name,
                                created_at=datetime.now().isoformat()
                            )

                            # 創建關係
                            session.run("""
                                MATCH (artwork:Artwork {europeana_id: $europeana_id})
                                MATCH (artist:Artist {name: $artist_name})
                                MERGE (artist)-[:CREATED]->(artwork)
                                """,
                                europeana_id=artwork_properties['europeana_id'],
                                artist_name=creator_name
                            )

                    # 處理提供者/博物館
                    provider = item.get('provider', '')
                    if provider:
                        session.run("""
                            MERGE (museum:Museum {name: $name})
                            SET museum.country = $country,
                                museum.source = 'Europeana',
                                museum.created_at = $created_at
                            """,
                            name=provider,
                            country=item.get('country', ''),
                            created_at=datetime.now().isoformat()
                        )

                        session.run("""
                            MATCH (artwork:Artwork {europeana_id: $europeana_id})
                            MATCH (museum:Museum {name: $museum_name})
                            MERGE (artwork)-[:HOUSED_IN]->(museum)
                            """,
                            europeana_id=artwork_properties['europeana_id'],
                            museum_name=provider
                        )

                    # 處理藝術史分類
                    categories = item.get('artHistoryCategories', [])
                    for category in categories:
                        if ':' in category:
                            cat_type, cat_value = category.split(':', 1)

                            if cat_type == 'period':
                                # 創建時期
                                session.run("""
                                    MERGE (period:Period {name: $name})
                                    SET period.source = 'Europeana',
                                        period.created_at = $created_at
                                    """,
                                    name=cat_value.title(),
                                    created_at=datetime.now().isoformat()
                                )

                                session.run("""
                                    MATCH (artwork:Artwork {europeana_id: $europeana_id})
                                    MATCH (period:Period {name: $period_name})
                                    MERGE (artwork)-[:FROM_PERIOD]->(period)
                                    """,
                                    europeana_id=artwork_properties['europeana_id'],
                                    period_name=cat_value.title()
                                )

                    processed_count += 1

                except Exception as e:
                    logger.error(f"❌ 處理Europeana項目失敗: {e}")

        return processed_count

    def process_met_data(self, data: List) -> int:
        """處理Met Museum數據"""
        processed_count = 0

        with self.driver.session() as session:
            for item in data:
                try:
                    # 創建藝術作品節點
                    artwork_properties = {
                        'met_id': str(item.get('id', '')),
                        'title': self.clean_text(item.get('title', 'Unknown')),
                        'artist': self.clean_text(item.get('artist', '')),
                        'date': item.get('date', ''),
                        'medium': item.get('medium', ''),
                        'dimensions': item.get('dimensions', ''),
                        'culture': item.get('culture', ''),
                        'department': item.get('department', ''),
                        'image_url': item.get('imageUrl', ''),
                        'url': item.get('url', ''),
                        'source': 'Met Museum',
                        'created_at': datetime.now().isoformat()
                    }

                    # 創建藝術作品
                    session.run("""
                        MERGE (artwork:Artwork {met_id: $met_id})
                        SET artwork += $props
                        """,
                        met_id=artwork_properties['met_id'],
                        props=artwork_properties
                    )

                    # 處理藝術家
                    artist_name = item.get('artist', '')
                    if artist_name and artist_name.strip() and artist_name != 'Unknown':
                        artist_name = self.clean_text(artist_name)

                        # 提取國籍和年代信息
                        nationality = item.get('artistNationality', '')
                        begin_date = item.get('artistBeginDate', '')
                        end_date = item.get('artistEndDate', '')

                        # 創建藝術家
                        artist_props = {
                            'name': artist_name,
                            'nationality': nationality,
                            'birth_year': begin_date,
                            'death_year': end_date,
                            'source': 'Met Museum',
                            'created_at': datetime.now().isoformat()
                        }

                        session.run("""
                            MERGE (artist:Artist {name: $name})
                            SET artist += $props
                            """,
                            name=artist_name,
                            props=artist_props
                        )

                        # 創建關係
                        session.run("""
                            MATCH (artwork:Artwork {met_id: $met_id})
                            MATCH (artist:Artist {name: $artist_name})
                            MERGE (artist)-[:CREATED]->(artwork)
                            """,
                            met_id=artwork_properties['met_id'],
                            artist_name=artist_name
                        )

                    # 處理部門作為博物館
                    department = item.get('department', '')
                    if department:
                        session.run("""
                            MERGE (museum:Museum {name: $name})
                            SET museum.type = 'Department',
                                museum.source = 'Met Museum',
                                museum.created_at = $created_at
                            """,
                            name=f"Met Museum - {department}",
                            created_at=datetime.now().isoformat()
                        )

                        session.run("""
                            MATCH (artwork:Artwork {met_id: $met_id})
                            MATCH (museum:Museum {name: $museum_name})
                            MERGE (artwork)-[:HOUSED_IN]->(museum)
                            """,
                            met_id=artwork_properties['met_id'],
                            museum_name=f"Met Museum - {department}"
                        )

                    processed_count += 1

                except Exception as e:
                    logger.error(f"❌ 處理Met Museum項目失敗: {e}")

        return processed_count

    def process_books_data(self, data: List) -> int:
        """處理Google Books數據"""
        processed_count = 0

        with self.driver.session() as session:
            for item in data:
                try:
                    # 創建書籍節點（作為資源）
                    book_properties = {
                        'google_id': item.get('id', ''),
                        'title': self.clean_text(item.get('title', 'Unknown')),
                        'authors': ', '.join(item.get('authors', [])),
                        'publisher': item.get('publisher', ''),
                        'published_date': item.get('publishedDate', ''),
                        'description': self.clean_text(item.get('description', '')),
                        'page_count': item.get('pageCount', 0),
                        'thumbnail': item.get('thumbnail', ''),
                        'preview_link': item.get('previewLink', ''),
                        'info_link': item.get('infoLink', ''),
                        'source': 'Google Books',
                        'created_at': datetime.now().isoformat()
                    }

                    # 創建資源節點
                    session.run("""
                        MERGE (resource:Resource {google_id: $google_id})
                        SET resource += $props,
                            resource:Book
                        """,
                        google_id=book_properties['google_id'],
                        props=book_properties
                    )

                    # 處理作者
                    authors = item.get('authors', [])
                    for author_name in authors:
                        if author_name and author_name.strip():
                            author_name = self.clean_text(author_name)

                            session.run("""
                                MERGE (author:Author {name: $name})
                                SET author.source = 'Google Books',
                                    author.created_at = $created_at
                                """,
                                name=author_name,
                                created_at=datetime.now().isoformat()
                            )

                            session.run("""
                                MATCH (resource:Resource {google_id: $google_id})
                                MATCH (author:Author {name: $author_name})
                                MERGE (author)-[:WROTE]->(resource)
                                """,
                                google_id=book_properties['google_id'],
                                author_name=author_name
                            )

                    processed_count += 1

                except Exception as e:
                    logger.error(f"❌ 處理Google Books項目失敗: {e}")

        return processed_count

    def clean_text(self, text: str) -> str:
        """清理文本"""
        if not text:
            return ""

        # 移除HTML標籤
        text = re.sub(r'<[^>]+>', '', text)
        # 移除多餘空白
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def get_import_statistics(self):
        """獲取導入統計"""
        if not self.driver:
            return {}

        with self.driver.session() as session:
            # 統計各類型節點數量
            result = session.run("""
                MATCH (n)
                RETURN labels(n) as labels, count(n) as count
                ORDER BY count DESC
            """)

            statistics = {}
            for record in result:
                label = record["labels"][0] if record["labels"] else "Unknown"
                statistics[label] = record["count"]

            # 統計關係數量
            rel_result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as rel_type, count(r) as count
                ORDER BY count DESC
            """)

            relationships = {}
            for record in rel_result:
                relationships[record["rel_type"]] = record["count"]

            return {
                "nodes": statistics,
                "relationships": relationships
            }

def main():
    """主函數"""
    print("🚀 開始導入爬蟲數據到Neo4j...")

    processor = CrawlerDataProcessor()
    success = processor.process_all_crawler_data()

    if success:
        print("\n📊 導入統計:")
        stats = processor.get_import_statistics()

        print("  節點統計:")
        for label, count in stats.get("nodes", {}).items():
            print(f"    {label}: {count}")

        print("  關係統計:")
        for rel_type, count in stats.get("relationships", {}).items():
            print(f"    {rel_type}: {count}")

        print("\n🎉 數據導入完成！")
    else:
        print("❌ 數據導入失敗")

if __name__ == "__main__":
    main()