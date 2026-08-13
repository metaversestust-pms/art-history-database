#!/usr/bin/env python3
"""
增強版向量資料庫整合腳本
將增強後的藝術史資料向量化並整合到ChromaDB v2和Neo4j
"""

import json
import os
import glob
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import requests
import chromadb
from chromadb.config import Settings as ChromaSettings
from neo4j import GraphDatabase

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnhancedDataIntegrator:
    """增強版資料整合器"""

    def __init__(self):
        """初始化整合器"""
        # 環境變數
        self.chromadb_host = os.getenv('CHROMADB_HOST', 'localhost')
        self.chromadb_port = int(os.getenv('CHROMADB_PORT', '8001'))
        self.neo4j_uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        self.neo4j_user = os.getenv('NEO4J_USER', 'neo4j')
        self.neo4j_password = os.getenv('NEO4J_PASSWORD', 'arthistory123')
        self.ollama_base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')

        # 資料目錄
        self.data_dir = Path(__file__).parent / 'data' / 'enhanced'

        # 連接
        self.chroma_client = None
        self.neo4j_driver = None
        self.collection = None

        # 統計
        self.stats = {
            'total_files': 0,
            'processed_files': 0,
            'total_items': 0,
            'vectorized_items': 0,
            'neo4j_items': 0,
            'with_chinese_labels': 0,
            'with_period_tags': 0,
            'errors': [],
            'start_time': datetime.now()
        }

    def connect_services(self):
        """連接所有服務"""
        logger.info("🔌 連接服務...")

        # 連接 ChromaDB (v2 API)
        try:
            logger.info(f"連接 ChromaDB v2: {self.chromadb_host}:{self.chromadb_port}")
            self.chroma_client = chromadb.HttpClient(
                host=self.chromadb_host,
                port=self.chromadb_port
            )
            self.chroma_client.heartbeat()
            logger.info("✅ ChromaDB 連接成功")

            # 獲取或創建集合
            try:
                self.collection = self.chroma_client.get_or_create_collection(
                    name="art_history_enhanced",
                    metadata={"description": "增強版藝術史知識庫（包含中文標籤）"}
                )
                current_count = self.collection.count()
                logger.info(f"✅ 集合 'art_history_enhanced' 準備就緒 (當前文檔數: {current_count})")
            except Exception as e:
                logger.warning(f"獲取集合時出現警告: {e}")
                # 嘗試創建新集合
                self.collection = self.chroma_client.create_collection(
                    name=f"art_history_enhanced_{int(datetime.now().timestamp())}",
                    metadata={"description": "增強版藝術史知識庫（包含中文標籤）"}
                )
                logger.info("✅ 已創建新集合")

        except Exception as e:
            logger.error(f"❌ ChromaDB 連接失敗: {e}")
            self.stats['errors'].append(f"ChromaDB 連接失敗: {e}")

        # 連接 Neo4j
        try:
            logger.info(f"連接 Neo4j: {self.neo4j_uri}")
            self.neo4j_driver = GraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_user, self.neo4j_password)
            )
            self.neo4j_driver.verify_connectivity()
            logger.info("✅ Neo4j 連接成功")

        except Exception as e:
            logger.error(f"❌ Neo4j 連接失敗: {e}")
            self.stats['errors'].append(f"Neo4j 連接失敗: {e}")

        # 測試 Ollama 連接
        try:
            logger.info(f"測試 Ollama: {self.ollama_base_url}")
            response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                logger.info("✅ Ollama 連接成功")
            else:
                raise Exception(f"狀態碼: {response.status_code}")
        except Exception as e:
            logger.warning(f"⚠️ Ollama 連接失敗: {e}")

    def create_enhanced_text_representation(self, artwork: Dict[str, Any]) -> str:
        """創建增強的文本表示（包含中英文標籤）"""
        parts = []

        # 基本資訊（英文）
        if artwork.get('title'):
            parts.append(f"Title: {artwork['title']}")

        if artwork.get('artist'):
            parts.append(f"Artist: {artwork['artist']}")

        if artwork.get('date'):
            parts.append(f"Date: {artwork['date']}")

        # 加入中文標籤（這是關鍵改進！）
        if artwork.get('artist_chinese'):
            parts.append(f"藝術家: {', '.join(artwork['artist_chinese'])}")
            self.stats['with_chinese_labels'] += 1

        # 時期標籤（中英文）
        if artwork.get('period_tags'):
            period = artwork['period_tags']
            if period.get('en'):
                parts.append(f"Period: {', '.join(period['en'])}")
                self.stats['with_period_tags'] += 1
            if period.get('zh'):
                parts.append(f"時期: {', '.join(period['zh'])}")

        # 類型標籤（中英文）
        if artwork.get('type_tags'):
            type_tags = artwork['type_tags']
            if type_tags.get('en'):
                parts.append(f"Type: {', '.join(type_tags['en'])}")
            if type_tags.get('zh'):
                parts.append(f"類型: {', '.join(type_tags['zh'])}")

        # 材料標籤（中英文）
        if artwork.get('material_tags'):
            material_tags = artwork['material_tags']
            if material_tags.get('en'):
                parts.append(f"Material: {', '.join(material_tags['en'])}")
            if material_tags.get('zh'):
                parts.append(f"材料: {', '.join(material_tags['zh'])}")

        # 概念標籤（中英文）
        if artwork.get('concept_tags'):
            concept_tags = artwork['concept_tags']
            if concept_tags.get('en'):
                parts.append(f"Concepts: {', '.join(concept_tags['en'])}")
            if concept_tags.get('zh'):
                parts.append(f"概念: {', '.join(concept_tags['zh'])}")

        # 所有標籤
        if artwork.get('all_tags'):
            parts.append(f"Tags: {', '.join(artwork['all_tags'][:20])}")  # 限制數量

        # 中文搜尋文本
        if artwork.get('search_text_chinese'):
            parts.append(f"中文標籤: {artwork['search_text_chinese']}")

        # 媒材
        if artwork.get('medium'):
            parts.append(f"Medium: {artwork['medium']}")

        # 文化
        if artwork.get('culture'):
            parts.append(f"Culture: {artwork['culture']}")

        # 描述
        if artwork.get('description'):
            desc = str(artwork['description'])[:500]  # 限制長度
            parts.append(f"Description: {desc}")

        return "\n".join(parts)

    def add_to_chromadb(self, artworks: List[Dict[str, Any]]):
        """批量添加到ChromaDB"""
        if not self.collection or not artworks:
            return

        logger.info(f"📝 向ChromaDB添加 {len(artworks)} 個藝術品...")

        try:
            # 準備資料
            documents = []
            metadatas = []
            ids = []

            for artwork in artworks:
                # 使用增強的文本表示
                text = self.create_enhanced_text_representation(artwork)
                documents.append(text)

                # 準備元資料（只保留字串和數字）
                metadata = {
                    'title': str(artwork.get('title', 'Untitled'))[:500],
                    'artist': str(artwork.get('artist', 'Unknown'))[:200],
                    'date': str(artwork.get('date', ''))[:100],
                    'source': str(artwork.get('source', 'enhanced'))[:100]
                }

                # 加入時期資訊
                if artwork.get('period_tags', {}).get('en'):
                    metadata['period'] = ', '.join(artwork['period_tags']['en'][:3])[:100]

                # 加入是否有中文標籤的標記
                if artwork.get('artist_chinese') or artwork.get('search_text_chinese'):
                    metadata['has_chinese'] = 'true'

                metadatas.append(metadata)

                # 生成唯一ID
                unique_id = f"{artwork.get('source', 'enhanced')}_{artwork.get('id', hash(str(artwork)))}".replace('/', '_')[:64]
                ids.append(unique_id)

            # 批量添加
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )

            self.stats['vectorized_items'] += len(artworks)
            logger.info(f"✅ 成功向量化 {len(artworks)} 個藝術品")

        except Exception as e:
            logger.error(f"❌ ChromaDB 添加失敗: {e}")
            self.stats['errors'].append(f"ChromaDB 添加失敗: {e}")

    def add_to_neo4j(self, artworks: List[Dict[str, Any]]):
        """批量添加到Neo4j"""
        if not self.neo4j_driver or not artworks:
            return

        logger.info(f"🕸️ 向Neo4j添加 {len(artworks)} 個藝術品...")

        try:
            with self.neo4j_driver.session() as session:
                for artwork in artworks:
                    # 創建或更新Artwork節點
                    session.run("""
                        MERGE (a:Artwork {id: $id})
                        SET a.title = $title,
                            a.date = $date,
                            a.medium = $medium,
                            a.culture = $culture,
                            a.source = $source,
                            a.description = $description,
                            a.has_chinese_labels = $has_chinese,
                            a.updated_at = datetime()
                    """, {
                        'id': str(artwork.get('id', hash(str(artwork)))),
                        'title': artwork.get('title', 'Untitled'),
                        'date': str(artwork.get('date', '')),
                        'medium': str(artwork.get('medium', ''))[:1000],
                        'culture': str(artwork.get('culture', '')),
                        'source': str(artwork.get('source', 'enhanced')),
                        'description': str(artwork.get('description', ''))[:1000],
                        'has_chinese': bool(artwork.get('artist_chinese') or artwork.get('search_text_chinese'))
                    })

                    # 如果有藝術家，創建Artist節點和關係
                    if artwork.get('artist') and artwork['artist'] != 'Unknown':
                        # 創建英文藝術家節點
                        session.run("""
                            MERGE (artist:Artist {name: $artist_name})
                            SET artist.name_en = $artist_name
                            WITH artist
                            MATCH (artwork:Artwork {id: $artwork_id})
                            MERGE (artist)-[:CREATED]->(artwork)
                        """, {
                            'artist_name': artwork['artist'],
                            'artwork_id': str(artwork.get('id', hash(str(artwork))))
                        })

                        # 如果有中文藝術家名，添加中文標籤
                        if artwork.get('artist_chinese'):
                            session.run("""
                                MATCH (artist:Artist {name: $artist_name})
                                SET artist.name_zh = $artist_chinese
                            """, {
                                'artist_name': artwork['artist'],
                                'artist_chinese': ', '.join(artwork['artist_chinese'])
                            })

                    # 如果有時期標籤，創建Period節點和關係
                    if artwork.get('period_tags', {}).get('en'):
                        for period_en in artwork['period_tags']['en']:
                            period_zh = ', '.join(artwork['period_tags'].get('zh', []))
                            session.run("""
                                MERGE (period:Period {name: $period_name})
                                SET period.name_en = $period_name,
                                    period.name_zh = $period_zh
                                WITH period
                                MATCH (artwork:Artwork {id: $artwork_id})
                                MERGE (artwork)-[:BELONGS_TO_PERIOD]->(period)
                            """, {
                                'period_name': period_en,
                                'period_zh': period_zh,
                                'artwork_id': str(artwork.get('id', hash(str(artwork))))
                            })

            self.stats['neo4j_items'] += len(artworks)
            logger.info(f"✅ 成功添加 {len(artworks)} 個藝術品到Neo4j")

        except Exception as e:
            logger.error(f"❌ Neo4j 添加失敗: {e}")
            self.stats['errors'].append(f"Neo4j 添加失敗: {e}")

    def process_enhanced_file(self, file_path: Path):
        """處理單個增強後的資料文件"""
        logger.info(f"📂 處理文件: {file_path.name}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                artworks = json.load(f)

            if not artworks:
                logger.warning(f"⚠️ 文件中沒有資料: {file_path.name}")
                return

            self.stats['total_items'] += len(artworks)
            logger.info(f"  提取了 {len(artworks)} 個藝術品")

            # 批量處理（每次50個）
            batch_size = 50
            for i in range(0, len(artworks), batch_size):
                batch = artworks[i:i + batch_size]

                # 添加到ChromaDB
                if self.collection:
                    self.add_to_chromadb(batch)

                # 添加到Neo4j
                if self.neo4j_driver:
                    self.add_to_neo4j(batch)

            self.stats['processed_files'] += 1

        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON 解析失敗: {file_path.name} - {e}")
            self.stats['errors'].append(f"JSON 解析失敗: {file_path.name}")
        except Exception as e:
            logger.error(f"❌ 處理文件失敗: {file_path.name} - {e}")
            self.stats['errors'].append(f"處理文件失敗: {file_path.name} - {e}")

    def print_summary(self):
        """打印統計摘要"""
        duration = (datetime.now() - self.stats['start_time']).total_seconds()

        logger.info("\n" + "=" * 70)
        logger.info("📊 增強版向量資料庫整合摘要")
        logger.info("=" * 70)
        logger.info(f"處理文件: {self.stats['processed_files']}/{self.stats['total_files']}")
        logger.info(f"總藝術品數: {self.stats['total_items']}")
        logger.info(f"向量化項目: {self.stats['vectorized_items']}")
        logger.info(f"Neo4j項目: {self.stats['neo4j_items']}")
        logger.info(f"包含中文標籤: {self.stats['with_chinese_labels']} ({self.stats['with_chinese_labels']/self.stats['total_items']*100:.1f}%)")
        logger.info(f"包含時期標籤: {self.stats['with_period_tags']} ({self.stats['with_period_tags']/self.stats['total_items']*100:.1f}%)")
        logger.info(f"耗時: {duration:.1f} 秒")

        if self.stats['errors']:
            logger.info(f"\n⚠️ 錯誤 ({len(self.stats['errors'])}):")
            for error in self.stats['errors'][:10]:
                logger.info(f"  - {error}")

        logger.info("=" * 70 + "\n")

    def run(self):
        """執行整合流程"""
        logger.info("🚀 開始增強版向量資料庫整合...")
        logger.info(f"📁 資料目錄: {self.data_dir}")

        try:
            # 連接服務
            self.connect_services()

            # 加載增強後的資料文件
            files = list(self.data_dir.glob('enhanced_*.json'))
            self.stats['total_files'] = len(files)

            if not files:
                logger.warning(f"⚠️ 在 {self.data_dir} 中沒有找到增強後的資料文件")
                return

            logger.info(f"📊 找到 {len(files)} 個增強後的資料文件\n")

            # 處理每個文件
            for file_path in files:
                self.process_enhanced_file(file_path)

            # 打印摘要
            self.print_summary()

            logger.info("✅ 增強版向量資料庫整合完成！")
            logger.info("\n下一步：")
            logger.info("  1. 測試中文查詢: curl -X POST http://localhost:8008/query -d '{\"query\": \"達文西的作品\"}'")
            logger.info("  2. 在OpenWebUI測試: http://localhost:8080")

        except Exception as e:
            logger.error(f"❌ 整合失敗: {e}")
            raise
        finally:
            # 關閉連接
            if self.neo4j_driver:
                self.neo4j_driver.close()

def main():
    """主程序"""
    integrator = EnhancedDataIntegrator()
    integrator.run()

if __name__ == '__main__':
    main()
