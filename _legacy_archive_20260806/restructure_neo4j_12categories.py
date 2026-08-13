#!/usr/bin/env python3
"""
Neo4j 資料重構腳本 - 12 大類藝術史分類系統

將簡單的 Artwork/Artist 結構重構為 12 大類詳細分類：
1. 人物 (Person)
2. 作品 (Artwork)
3. 流派/運動 (Style/Movement)
4. 技法與材質 (Technique/Material)
5. 主題與圖像學 (Theme/Iconography)
6. 時間 (Period/Chronology)
7. 地點 (Place)
8. 機構 (Institution)
9. 事件 (Event)
10. 文獻 (Source/Text)
11. 概念與術語 (Concept/Term)
12. 版本/語言 (Translation/Mapping)
"""

import logging
import re
from typing import Dict, List, Set
from neo4j import GraphDatabase

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ArtHistoryRestructurer:
    """藝術史資料庫重構器"""

    def __init__(self):
        self.uri = "bolt://localhost:7687"
        self.user = "neo4j"
        self.password = "arthistory123"
        self.driver = None

        # 藝術史時期定義
        self.period_mapping = {
            'renaissance': {
                'name_zh': '文藝復興',
                'name_en': 'Renaissance',
                'name_it': 'Rinascimento',
                'start_year': 1400,
                'end_year': 1600,
                'sub_periods': ['Early Renaissance', 'High Renaissance', 'Late Renaissance']
            },
            'baroque': {
                'name_zh': '巴洛克',
                'name_en': 'Baroque',
                'name_it': 'Barocco',
                'start_year': 1600,
                'end_year': 1750,
                'sub_periods': ['Early Baroque', 'High Baroque', 'Late Baroque']
            },
            'baroque_rococo': {
                'name_zh': '巴洛克與洛可可',
                'name_en': 'Baroque and Rococo',
                'start_year': 1600,
                'end_year': 1780,
                'sub_periods': ['Baroque', 'Rococo']
            },
            'medieval': {
                'name_zh': '中世紀',
                'name_en': 'Medieval',
                'start_year': 500,
                'end_year': 1400,
                'sub_periods': ['Early Medieval', 'Romanesque', 'Gothic']
            },
            'neoclassical_romantic': {
                'name_zh': '新古典主義與浪漫主義',
                'name_en': 'Neoclassical and Romantic',
                'start_year': 1750,
                'end_year': 1850,
                'sub_periods': ['Neoclassicism', 'Romanticism']
            }
        }

        # 技法關鍵字映射
        self.technique_keywords = {
            'oil': {'name_zh': '油彩', 'name_en': 'Oil Painting', 'name_it': 'Pittura a olio'},
            'tempera': {'name_zh': '蛋彩', 'name_en': 'Tempera', 'name_it': 'Tempera'},
            'fresco': {'name_zh': '壁畫', 'name_en': 'Fresco', 'name_it': 'Affresco'},
            'watercolor': {'name_zh': '水彩', 'name_en': 'Watercolor', 'name_it': 'Acquerello'},
            'engraving': {'name_zh': '版畫', 'name_en': 'Engraving', 'name_it': 'Incisione'},
            'etching': {'name_zh': '蝕刻', 'name_en': 'Etching', 'name_it': 'Acquaforte'},
            'woodcut': {'name_zh': '木刻', 'name_en': 'Woodcut', 'name_it': 'Xilografia'},
            'sculpture': {'name_zh': '雕塑', 'name_en': 'Sculpture', 'name_it': 'Scultura'},
            'marble': {'name_zh': '大理石', 'name_en': 'Marble', 'name_it': 'Marmo'},
            'bronze': {'name_zh': '青銅', 'name_en': 'Bronze', 'name_it': 'Bronzo'},
            'drawing': {'name_zh': '素描', 'name_en': 'Drawing', 'name_it': 'Disegno'}
        }

        # 主題關鍵字映射
        self.theme_keywords = {
            'religious': {'name_zh': '宗教題材', 'keywords': ['Madonna', 'Christ', 'Saint', 'Virgin', 'Crucifixion', 'Annunciation']},
            'mythological': {'name_zh': '神話題材', 'keywords': ['Venus', 'Apollo', 'Diana', 'Jupiter', 'Bacchus', 'Cupid']},
            'portrait': {'name_zh': '肖像畫', 'keywords': ['Portrait', 'Self-Portrait', 'Bust']},
            'landscape': {'name_zh': '風景畫', 'keywords': ['Landscape', 'View', 'Scene']},
            'still_life': {'name_zh': '靜物畫', 'keywords': ['Still Life', 'Vanitas']},
            'allegory': {'name_zh': '寓意畫', 'keywords': ['Allegory', 'Virtue', 'Vice']}
        }

        # 藝術術語定義
        self.art_concepts = {
            'sfumato': {
                'name_zh': '暈塗法',
                'name_en': 'Sfumato',
                'name_it': 'Sfumato',
                'definition': '微妙的色彩漸層技法，創造柔和模糊的輪廓',
                'associated_artists': ['Leonardo da Vinci']
            },
            'chiaroscuro': {
                'name_zh': '明暗對比法',
                'name_en': 'Chiaroscuro',
                'name_it': 'Chiaroscuro',
                'definition': '運用強烈的明暗對比營造立體感',
                'associated_artists': ['Caravaggio', 'Rembrandt']
            },
            'contrapposto': {
                'name_zh': '對立式平衡',
                'name_en': 'Contrapposto',
                'name_it': 'Contrapposto',
                'definition': '人體重心放在一腳上，產生S形曲線',
                'associated_artists': ['Michelangelo', 'Donatello']
            },
            'perspective': {
                'name_zh': '透視法',
                'name_en': 'Linear Perspective',
                'name_it': 'Prospettiva',
                'definition': '使用數學原理在平面上創造三維空間錯覺',
                'associated_artists': ['Brunelleschi', 'Alberti', 'Piero della Francesca']
            },
            'tenebrism': {
                'name_zh': '暗色主義',
                'name_en': 'Tenebrism',
                'name_it': 'Tenebrismo',
                'definition': '使用極端明暗對比，大面積暗色背景',
                'associated_artists': ['Caravaggio']
            }
        }

    def connect(self):
        """連接 Neo4j"""
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            with self.driver.session() as session:
                result = session.run("RETURN 1")
                result.single()
            logger.info("✅ 成功連接 Neo4j")
            return True
        except Exception as e:
            logger.error(f"❌ Neo4j 連接失敗: {e}")
            return False

    def create_indexes(self):
        """創建索引以提升查詢效能"""
        logger.info("\n📊 創建索引...")

        indexes = [
            # 1. 人物索引
            "CREATE INDEX person_name IF NOT EXISTS FOR (p:Person) ON (p.name)",
            "CREATE INDEX person_name_zh IF NOT EXISTS FOR (p:Person) ON (p.name_zh)",

            # 2. 作品索引
            "CREATE INDEX artwork_id IF NOT EXISTS FOR (a:Artwork) ON (a.objectID)",
            "CREATE INDEX artwork_title IF NOT EXISTS FOR (a:Artwork) ON (a.title)",

            # 3. 流派索引
            "CREATE INDEX style_name IF NOT EXISTS FOR (s:Style) ON (s.name)",

            # 4. 技法索引
            "CREATE INDEX technique_name IF NOT EXISTS FOR (t:Technique) ON (t.name)",

            # 5. 主題索引
            "CREATE INDEX theme_name IF NOT EXISTS FOR (th:Theme) ON (th.name)",

            # 6. 時期索引
            "CREATE INDEX period_name IF NOT EXISTS FOR (p:Period) ON (p.name)",

            # 7. 地點索引
            "CREATE INDEX place_name IF NOT EXISTS FOR (pl:Place) ON (pl.name)",

            # 8. 機構索引
            "CREATE INDEX institution_name IF NOT EXISTS FOR (i:Institution) ON (i.name)",

            # 9. 概念索引
            "CREATE INDEX concept_name IF NOT EXISTS FOR (c:Concept) ON (c.name)",
        ]

        with self.driver.session() as session:
            for idx_query in indexes:
                try:
                    session.run(idx_query)
                    logger.info(f"  ✓ {idx_query.split()[2]}")
                except Exception as e:
                    logger.warning(f"  ⚠️ 索引可能已存在: {e}")

    def restructure_artists_to_persons(self):
        """1. 重構藝術家節點為人物節點"""
        logger.info("\n👤 1. 重構 Artist → Person...")

        query = """
        MATCH (a:Artist)
        MERGE (p:Person {name: a.name})
        SET p.name_en = a.name,
            p.period = a.period,
            p.role = 'Artist',
            p.updated_at = datetime()
        WITH a, p
        MATCH (a)-[r:CREATED]->(artwork:Artwork)
        MERGE (p)-[:CREATED]->(artwork)
        DELETE r
        WITH a, count(*) as rel_count
        DETACH DELETE a
        RETURN count(*) as processed
        """

        with self.driver.session() as session:
            result = session.run(query)
            count = result.single()['processed']
            logger.info(f"  ✅ 已轉換 {count} 位藝術家為人物節點")

    def create_period_nodes(self):
        """6. 創建時期節點"""
        logger.info("\n📅 6. 創建時期節點...")

        with self.driver.session() as session:
            for period_key, period_info in self.period_mapping.items():
                # 創建主要時期節點
                query = """
                MERGE (p:Period {name: $name_en})
                SET p.name_zh = $name_zh,
                    p.name_it = $name_it,
                    p.start_year = $start_year,
                    p.end_year = $end_year,
                    p.category = 'Major Period',
                    p.updated_at = datetime()
                RETURN p.name as created
                """

                result = session.run(query,
                    name_en=period_info['name_en'],
                    name_zh=period_info.get('name_zh', ''),
                    name_it=period_info.get('name_it', ''),
                    start_year=period_info['start_year'],
                    end_year=period_info['end_year']
                )
                created = result.single()['created']
                logger.info(f"  ✓ 創建時期: {created}")

                # 創建子時期節點
                for sub_period in period_info.get('sub_periods', []):
                    sub_query = """
                    MERGE (sp:Period {name: $name})
                    SET sp.category = 'Sub Period',
                        sp.parent_period = $parent,
                        sp.updated_at = datetime()
                    WITH sp
                    MATCH (p:Period {name: $parent})
                    MERGE (sp)-[:PART_OF]->(p)
                    """
                    session.run(sub_query, name=sub_period, parent=period_info['name_en'])

    def link_artworks_to_periods(self):
        """連接作品到時期節點"""
        logger.info("\n🔗 連接作品到時期節點...")

        query = """
        MATCH (a:Artwork)
        WHERE a.period IS NOT NULL
        WITH a,
             CASE a.period
                 WHEN 'renaissance' THEN 'Renaissance'
                 WHEN 'baroque' THEN 'Baroque'
                 WHEN 'baroque_rococo' THEN 'Baroque and Rococo'
                 WHEN 'medieval' THEN 'Medieval'
                 WHEN 'neoclassical_romantic' THEN 'Neoclassical and Romantic'
                 ELSE a.period
             END as period_name
        MATCH (p:Period {name: period_name})
        MERGE (a)-[:BELONGS_TO_PERIOD]->(p)
        RETURN count(*) as linked
        """

        with self.driver.session() as session:
            result = session.run(query)
            count = result.single()['linked']
            logger.info(f"  ✅ 已連接 {count} 件作品到時期")

    def create_technique_nodes(self):
        """4. 創建技法與材質節點"""
        logger.info("\n🎨 4. 創建技法與材質節點...")

        with self.driver.session() as session:
            for tech_key, tech_info in self.technique_keywords.items():
                query = """
                MERGE (t:Technique {name: $name_en})
                SET t.name_zh = $name_zh,
                    t.name_it = $name_it,
                    t.updated_at = datetime()
                RETURN t.name as created
                """

                result = session.run(query,
                    name_en=tech_info['name_en'],
                    name_zh=tech_info['name_zh'],
                    name_it=tech_info.get('name_it', '')
                )
                created = result.single()['created']
                logger.info(f"  ✓ 創建技法: {created}")

    def link_artworks_to_techniques(self):
        """連接作品到技法節點（基於 medium 和 classification）"""
        logger.info("\n🔗 連接作品到技法節點...")

        count = 0
        with self.driver.session() as session:
            for tech_key, tech_info in self.technique_keywords.items():
                # 從 medium 欄位匹配
                query = """
                MATCH (a:Artwork)
                WHERE toLower(a.medium) CONTAINS $keyword
                   OR toLower(a.classification) CONTAINS $keyword
                WITH a LIMIT 1000
                MATCH (t:Technique {name: $name})
                MERGE (a)-[:USES_TECHNIQUE]->(t)
                RETURN count(*) as linked
                """

                result = session.run(query,
                    keyword=tech_key.lower(),
                    name=tech_info['name_en']
                )
                linked = result.single()['linked']
                if linked > 0:
                    count += linked
                    logger.info(f"  ✓ {tech_info['name_en']}: {linked} 件作品")

        logger.info(f"  ✅ 總計連接 {count} 個技法關聯")

    def create_theme_nodes(self):
        """5. 創建主題與圖像學節點"""
        logger.info("\n🎭 5. 創建主題與圖像學節點...")

        with self.driver.session() as session:
            for theme_key, theme_info in self.theme_keywords.items():
                query = """
                MERGE (th:Theme {name: $name_en})
                SET th.name_zh = $name_zh,
                    th.category = 'Iconography',
                    th.updated_at = datetime()
                RETURN th.name as created
                """

                result = session.run(query,
                    name_en=theme_key.replace('_', ' ').title(),
                    name_zh=theme_info['name_zh']
                )
                created = result.single()['created']
                logger.info(f"  ✓ 創建主題: {created}")

    def link_artworks_to_themes(self):
        """連接作品到主題節點（基於標題關鍵字）"""
        logger.info("\n🔗 連接作品到主題節點...")

        count = 0
        with self.driver.session() as session:
            for theme_key, theme_info in self.theme_keywords.items():
                theme_name = theme_key.replace('_', ' ').title()

                for keyword in theme_info['keywords']:
                    query = """
                    MATCH (a:Artwork)
                    WHERE a.title CONTAINS $keyword
                       OR a.description CONTAINS $keyword
                    WITH a LIMIT 500
                    MATCH (th:Theme {name: $theme_name})
                    MERGE (a)-[:HAS_THEME]->(th)
                    RETURN count(*) as linked
                    """

                    result = session.run(query,
                        keyword=keyword,
                        theme_name=theme_name
                    )
                    linked = result.single()['linked']
                    count += linked

                if count > 0:
                    logger.info(f"  ✓ {theme_name}: 已匹配")

        logger.info(f"  ✅ 總計連接 {count} 個主題關聯")

    def create_place_nodes(self):
        """7. 創建地點節點"""
        logger.info("\n🌍 7. 創建地點節點...")

        # 提取所有唯一的 culture 作為地點
        query = """
        MATCH (a:Artwork)
        WHERE a.culture IS NOT NULL AND a.culture <> ''
        WITH DISTINCT a.culture as culture_name
        MERGE (pl:Place {name: culture_name})
        SET pl.type = 'Culture/Region',
            pl.updated_at = datetime()
        RETURN count(*) as created
        """

        with self.driver.session() as session:
            result = session.run(query)
            count = result.single()['created']
            logger.info(f"  ✅ 創建 {count} 個地點/文化節點")

    def link_artworks_to_places(self):
        """連接作品到地點節點"""
        logger.info("\n🔗 連接作品到地點節點...")

        query = """
        MATCH (a:Artwork)
        WHERE a.culture IS NOT NULL AND a.culture <> ''
        WITH a
        MATCH (pl:Place {name: a.culture})
        MERGE (a)-[:FROM_PLACE]->(pl)
        RETURN count(*) as linked
        """

        with self.driver.session() as session:
            result = session.run(query)
            count = result.single()['linked']
            logger.info(f"  ✅ 已連接 {count} 件作品到地點")

    def create_institution_nodes(self):
        """8. 創建機構節點"""
        logger.info("\n🏛️ 8. 創建機構節點...")

        # 提取所有唯一的 department 和 source 作為機構
        query = """
        MATCH (a:Artwork)
        WHERE a.department IS NOT NULL AND a.department <> ''
        WITH DISTINCT a.department as dept_name
        MERGE (i:Institution {name: dept_name})
        SET i.type = 'Museum Department',
            i.updated_at = datetime()
        RETURN count(*) as created
        """

        with self.driver.session() as session:
            result = session.run(query)
            count = result.single()['created']
            logger.info(f"  ✅ 創建 {count} 個機構節點")

            # 創建主要博物館節點
            museums = [
                {'name': 'Harvard Art Museums', 'name_zh': '哈佛藝術博物館', 'type': 'Museum'},
                {'name': 'Met Museum', 'name_zh': '大都會藝術博物館', 'type': 'Museum'}
            ]

            for museum in museums:
                query2 = """
                MERGE (i:Institution {name: $name})
                SET i.name_zh = $name_zh,
                    i.type = $type,
                    i.updated_at = datetime()
                """
                session.run(query2, **museum)
                logger.info(f"  ✓ 創建博物館: {museum['name']}")

    def link_artworks_to_institutions(self):
        """連接作品到機構節點"""
        logger.info("\n🔗 連接作品到機構節點...")

        # 連接到部門
        query1 = """
        MATCH (a:Artwork)
        WHERE a.department IS NOT NULL AND a.department <> ''
        WITH a
        MATCH (i:Institution {name: a.department})
        MERGE (a)-[:COLLECTED_BY]->(i)
        RETURN count(*) as linked
        """

        # 連接到主要博物館
        query2 = """
        MATCH (a:Artwork)
        WHERE a.original_source IS NOT NULL
        WITH a
        MATCH (i:Institution {name: a.original_source})
        MERGE (a)-[:SOURCED_FROM]->(i)
        RETURN count(*) as linked
        """

        with self.driver.session() as session:
            result1 = session.run(query1)
            count1 = result1.single()['linked']
            logger.info(f"  ✓ 連接到部門: {count1} 件作品")

            result2 = session.run(query2)
            count2 = result2.single()['linked']
            logger.info(f"  ✓ 連接到博物館: {count2} 件作品")

    def create_concept_nodes(self):
        """11. 創建概念與術語節點"""
        logger.info("\n💡 11. 創建藝術概念節點...")

        with self.driver.session() as session:
            for concept_key, concept_info in self.art_concepts.items():
                query = """
                MERGE (c:Concept {name: $name_en})
                SET c.name_zh = $name_zh,
                    c.name_it = $name_it,
                    c.definition = $definition,
                    c.category = 'Art Technique Concept',
                    c.updated_at = datetime()
                RETURN c.name as created
                """

                result = session.run(query,
                    name_en=concept_info['name_en'],
                    name_zh=concept_info['name_zh'],
                    name_it=concept_info.get('name_it', ''),
                    definition=concept_info['definition']
                )
                created = result.single()['created']
                logger.info(f"  ✓ 創建概念: {created}")

                # 連接概念到相關藝術家
                for artist_name in concept_info.get('associated_artists', []):
                    link_query = """
                    MATCH (c:Concept {name: $concept_name})
                    MATCH (p:Person {name: $artist_name})
                    MERGE (p)-[:KNOWN_FOR]->(c)
                    """
                    session.run(link_query,
                        concept_name=concept_info['name_en'],
                        artist_name=artist_name
                    )
                    logger.info(f"    → 連接到藝術家: {artist_name}")

    def create_translation_mapping(self):
        """12. 創建多語言對照節點"""
        logger.info("\n🌐 12. 創建多語言對照...")

        # 為時期創建翻譯對照
        with self.driver.session() as session:
            query = """
            MATCH (p:Period)
            WHERE p.name_zh IS NOT NULL OR p.name_it IS NOT NULL
            MERGE (t:Translation {source: p.name})
            SET t.english = p.name,
                t.chinese = p.name_zh,
                t.italian = p.name_it,
                t.category = 'Period',
                t.updated_at = datetime()
            WITH t, p
            MERGE (p)-[:HAS_TRANSLATION]->(t)
            RETURN count(*) as created
            """
            result = session.run(query)
            count = result.single()['created']
            logger.info(f"  ✅ 創建 {count} 個時期翻譯對照")

            # 為技法創建翻譯對照
            query2 = """
            MATCH (t:Technique)
            WHERE t.name_zh IS NOT NULL
            MERGE (tr:Translation {source: t.name})
            SET tr.english = t.name,
                tr.chinese = t.name_zh,
                tr.italian = t.name_it,
                tr.category = 'Technique',
                tr.updated_at = datetime()
            WITH tr, t
            MERGE (t)-[:HAS_TRANSLATION]->(tr)
            RETURN count(*) as created
            """
            result2 = session.run(query2)
            count2 = result2.single()['created']
            logger.info(f"  ✅ 創建 {count2} 個技法翻譯對照")

    def generate_statistics(self):
        """生成重構後的統計報告"""
        logger.info("\n📊 生成統計報告...")

        stats_queries = [
            ("節點總數", "MATCH (n) RETURN count(n) as count"),
            ("關係總數", "MATCH ()-[r]->() RETURN count(r) as count"),
            ("人物數量", "MATCH (p:Person) RETURN count(p) as count"),
            ("作品數量", "MATCH (a:Artwork) RETURN count(a) as count"),
            ("時期數量", "MATCH (p:Period) RETURN count(p) as count"),
            ("技法數量", "MATCH (t:Technique) RETURN count(t) as count"),
            ("主題數量", "MATCH (th:Theme) RETURN count(th) as count"),
            ("地點數量", "MATCH (pl:Place) RETURN count(pl) as count"),
            ("機構數量", "MATCH (i:Institution) RETURN count(i) as count"),
            ("概念數量", "MATCH (c:Concept) RETURN count(c) as count"),
            ("翻譯對照數", "MATCH (t:Translation) RETURN count(t) as count"),
        ]

        stats = {}
        with self.driver.session() as session:
            for name, query in stats_queries:
                result = session.run(query)
                count = result.single()['count']
                stats[name] = count
                logger.info(f"  {name}: {count:,}")

            # 關係類型統計
            logger.info("\n  關係類型分布:")
            rel_query = """
            MATCH ()-[r]->()
            RETURN type(r) as rel_type, count(*) as count
            ORDER BY count DESC
            """
            result = session.run(rel_query)
            for record in result:
                logger.info(f"    - {record['rel_type']}: {record['count']:,}")

        return stats

    def run_restructure(self):
        """執行完整重構流程"""
        logger.info("="*80)
        logger.info("🎨 藝術史資料庫重構 - 12 大類分類系統")
        logger.info("="*80)

        if not self.connect():
            return

        try:
            # 創建索引
            self.create_indexes()

            # 1. 重構人物
            self.restructure_artists_to_persons()

            # 6. 創建時期節點
            self.create_period_nodes()
            self.link_artworks_to_periods()

            # 4. 創建技法節點
            self.create_technique_nodes()
            self.link_artworks_to_techniques()

            # 5. 創建主題節點
            self.create_theme_nodes()
            self.link_artworks_to_themes()

            # 7. 創建地點節點
            self.create_place_nodes()
            self.link_artworks_to_places()

            # 8. 創建機構節點
            self.create_institution_nodes()
            self.link_artworks_to_institutions()

            # 11. 創建概念節點
            self.create_concept_nodes()

            # 12. 創建翻譯對照
            self.create_translation_mapping()

            # 生成統計報告
            logger.info("\n" + "="*80)
            stats = self.generate_statistics()

            logger.info("\n" + "="*80)
            logger.info("✅ 重構完成！")
            logger.info("="*80)

            logger.info("\n💡 測試查詢範例:")
            logger.info("1. 查看所有節點類型:")
            logger.info("   MATCH (n) RETURN DISTINCT labels(n), count(*)")
            logger.info("\n2. 查看文藝復興時期的作品:")
            logger.info("   MATCH (a:Artwork)-[:BELONGS_TO_PERIOD]->(p:Period {name: 'Renaissance'})")
            logger.info("   RETURN a.title LIMIT 10")
            logger.info("\n3. 查看使用油彩技法的作品:")
            logger.info("   MATCH (a:Artwork)-[:USES_TECHNIQUE]->(t:Technique)")
            logger.info("   WHERE t.name CONTAINS 'Oil'")
            logger.info("   RETURN a.title, t.name_zh LIMIT 10")
            logger.info("\n4. 查看與 sfumato 概念相關的藝術家:")
            logger.info("   MATCH (p:Person)-[:KNOWN_FOR]->(c:Concept {name: 'Sfumato'})")
            logger.info("   RETURN p.name")

        finally:
            if self.driver:
                self.driver.close()
                logger.info("\n🔌 已關閉 Neo4j 連接")


def main():
    print("\n" + "="*80)
    print("🎨 Neo4j 資料庫重構工具 - 12 大類藝術史分類系統")
    print("="*80)
    print("\n此工具將重構您的 Neo4j 資料庫，建立以下分類：")
    print("1. 人物 (Person) - 藝術家、理論家、贊助人")
    print("2. 作品 (Artwork) - 保持現有作品資料")
    print("3. 流派/運動 (Style/Movement) - 待擴展")
    print("4. 技法與材質 (Technique) - 油彩、蛋彩、壁畫等")
    print("5. 主題與圖像學 (Theme) - 宗教、神話、肖像等")
    print("6. 時間 (Period) - 文藝復興、巴洛克等時期")
    print("7. 地點 (Place) - 城市、地區、文化")
    print("8. 機構 (Institution) - 博物館、部門")
    print("9. 事件 (Event) - 待擴展")
    print("10. 文獻 (Source/Text) - 待擴展")
    print("11. 概念與術語 (Concept) - sfumato、chiaroscuro 等")
    print("12. 版本/語言 (Translation) - 多語言對照")

    print("\n⚠️  注意：此操作將：")
    print("   - 保留所有現有的 Artwork 節點")
    print("   - 將 Artist 節點轉換為 Person 節點")
    print("   - 創建新的分類節點和關係")
    print("   - 不會刪除任何作品資料")

    confirm = input("\n確認開始重構？(yes/no): ").strip().lower()
    if confirm != 'yes':
        print("❌ 已取消")
        return

    restructurer = ArtHistoryRestructurer()
    restructurer.run_restructure()

    print("\n✅ 重構完成！")
    print("\n💡 建議下一步：")
    print("1. 在 Neo4j Browser 中測試查詢: http://localhost:7474")
    print("2. 使用 GraphRAG 測試新的知識圖譜結構")
    print("3. 根據需求繼續擴展其他分類（事件、文獻等）")


if __name__ == "__main__":
    main()
