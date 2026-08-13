#!/usr/bin/env python3
"""
向量資料庫整合腳本 (修復版)
將爬蟲收集的藝術史資料向量化並整合到ChromaDB和Neo4j
使用REST API直接訪問ChromaDB以避免客戶端版本問題
"""

import json
import os
import glob
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime, timedelta
from neo4j import GraphDatabase
import requests

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VectorDBIntegrator:
    """向量資料庫整合器"""

    def __init__(self):
        """初始化整合器"""
        # 環境變數
        self.chromadb_host = os.getenv('CHROMADB_HOST', 'localhost')
        self.chromadb_port = int(os.getenv('CHROMADB_PORT', '8001'))
        self.neo4j_uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        self.neo4j_user = os.getenv('NEO4J_USER', 'neo4j')
        self.neo4j_password = os.getenv('NEO4J_PASSWORD', 'arthistory123')
        self.ollama_base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')

        # ChromaDB REST API URL
        self.chromadb_base_url = f"http://{self.chromadb_host}:{self.chromadb_port}/api/v2"

        # 資料目錄
        self.data_dir = Path(__file__).parent / 'data' / 'raw'

        # 連接
        self.neo4j_driver = None
        self.collection_name = "art_history"

        # 統計
        self.stats = {
            'total_files': 0,
            'processed_files': 0,
            'total_items': 0,
            'vectorized_items': 0,
            'neo4j_items': 0,
            'errors': [],
            'start_time': datetime.now()
        }

    def connect_services(self):
        """連接所有服務"""
        logger.info("🔌 連接服務...")

        # 測試 ChromaDB (使用REST API)
        try:
            logger.info(f"連接 ChromaDB: {self.chromadb_base_url}")
            response = requests.get(f"{self.chromadb_base_url}/heartbeat", timeout=5)
            if response.status_code == 200:
                logger.info("✅ ChromaDB 連接成功")
                # 確保collection存在
                self.ensure_collection()
            else:
                raise Exception(f"狀態碼: {response.status_code}")
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

    def ensure_collection(self):
        """確保ChromaDB collection存在"""
        try:
            # 使用REST API創建或獲取collection
            response = requests.post(
                f"{self.chromadb_base_url}/collections",
                json={
                    "name": self.collection_name,
                    "metadata": {"description": "藝術史知識庫"}
                },
                timeout=10
            )

            if response.status_code in [200, 201]:
                logger.info(f"✅ Collection '{self.collection_name}' 準備就緒")
            elif response.status_code == 409:
                # Collection已存在
                logger.info(f"✅ Collection '{self.collection_name}' 已存在")
            else:
                logger.warning(f"⚠️ Collection創建響應: {response.status_code}")

        except Exception as e:
            logger.warning(f"⚠️ Collection創建失敗: {e}")

    def get_embedding(self, text: str) -> List[float]:
        """獲取文本的向量嵌入"""
        try:
            response = requests.post(
                f"{self.ollama_base_url}/api/embeddings",
                json={
                    "model": "nomic-embed-text",
                    "prompt": text
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                return result.get('embedding', [])
            else:
                return None

        except Exception as e:
            logger.warning(f"向量生成錯誤: {e}")
            return None

    def load_recent_data_files(self, hours=24) -> List[Path]:
        """加載最近的資料文件"""
        logger.info(f"🔍 搜尋最近 {hours} 小時內的資料文件...")

        all_files = list(self.data_dir.glob('*.json'))
        recent_files = []
        cutoff_time = datetime.now() - timedelta(hours=hours)

        for file_path in all_files:
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            if mtime > cutoff_time:
                recent_files.append(file_path)

        logger.info(f"找到 {len(recent_files)} 個最近的資料文件")
        self.stats['total_files'] = len(recent_files)

        return recent_files

    def normalize_artwork_data(self, item: Dict[str, Any], source: str) -> Dict[str, Any]:
        """標準化藝術品資料格式"""
        normalized = {
            'id': '',
            'title': '',
            'artist': '',
            'date': '',
            'description': '',
            'medium': '',
            'culture': '',
            'period': '',
            'source': source,
            'metadata': {}
        }

        # Met Museum 格式
        if 'objectID' in item:
            normalized['id'] = f"met_{item.get('objectID', '')}"
            normalized['title'] = item.get('title', 'Untitled')
            normalized['artist'] = item.get('artistDisplayName', item.get('artist', 'Unknown'))
            normalized['date'] = item.get('objectDate', item.get('date', ''))
            normalized['medium'] = item.get('medium', '')
            normalized['culture'] = item.get('culture', '')
            normalized['period'] = item.get('period', '')
            normalized['description'] = item.get('creditLine', '')

        # Harvard 格式
        elif 'harvardId' in item:
            normalized['id'] = f"harvard_{item.get('harvardId', '')}"
            normalized['title'] = item.get('title', 'Untitled')
            # Harvard people是list
            if item.get('people'):
                normalized['artist'] = ', '.join([p.get('name', '') for p in item['people'] if p.get('name')])
            normalized['date'] = item.get('dated', '')
            normalized['medium'] = item.get('medium', '')
            normalized['culture'] = item.get('culture', '')
            normalized['period'] = item.get('period', '')
            normalized['description'] = item.get('description', '')

        # Europeana 格式
        elif 'europeana_id' in str(item.get('id', '')).lower() or 'dcCreator' in item:
            normalized['id'] = str(item.get('id', f"euro_{hash(str(item))}"))
            normalized['title'] = item.get('title', ['Untitled'])[0] if isinstance(item.get('title'), list) else item.get('title', 'Untitled')
            normalized['artist'] = item.get('dcCreator', item.get('creator', 'Unknown'))
            normalized['date'] = str(item.get('year', item.get('date', '')))
            normalized['description'] = item.get('dcDescription', item.get('description', ''))
            normalized['culture'] = item.get('country', '')

        # 通用格式
        else:
            normalized['id'] = str(item.get('id', f"art_{hash(str(item))}"))
            normalized['title'] = item.get('title', item.get('name', 'Untitled'))
            normalized['artist'] = item.get('artist', item.get('creator', 'Unknown'))
            normalized['date'] = str(item.get('date', item.get('year', '')))
            normalized['description'] = item.get('description', '')
            normalized['medium'] = item.get('medium', item.get('type', ''))
            normalized['culture'] = item.get('culture', item.get('country', ''))
            normalized['period'] = item.get('period', '')

        return normalized

    def create_text_representation(self, artwork: Dict[str, Any]) -> str:
        """創建藝術品的文本表示（用於向量化）"""
        parts = []

        if artwork['title']:
            parts.append(f"Title: {artwork['title']}")
        if artwork['artist']:
            parts.append(f"Artist: {artwork['artist']}")
        if artwork['date']:
            parts.append(f"Date: {artwork['date']}")
        if artwork['culture']:
            parts.append(f"Culture: {artwork['culture']}")
        if artwork['period']:
            parts.append(f"Period: {artwork['period']}")
        if artwork['medium']:
            parts.append(f"Medium: {artwork['medium']}")
        if artwork['description']:
            parts.append(f"Description: {artwork['description']}")

        return "\n".join(parts)

    def add_to_chromadb(self, artworks: List[Dict[str, Any]]):
        """批量添加到ChromaDB (使用REST API)"""
        if not artworks:
            return

        logger.info(f"📝 向ChromaDB添加 {len(artworks)} 個藝術品...")

        try:
            # 準備資料
            documents = []
            metadatas = []
            ids = []

            for artwork in artworks:
                text = self.create_text_representation(artwork)
                documents.append(text)

                metadata = {
                    'title': str(artwork['title'])[:500],
                    'artist': str(artwork['artist'])[:200],
                    'date': str(artwork['date'])[:100],
                    'source': str(artwork['source'])[:100]
                }
                metadatas.append(metadata)

                unique_id = f"{artwork['source']}_{artwork['id']}".replace('/', '_').replace(' ', '_')[:64]
                ids.append(unique_id)

            # 使用REST API添加
            response = requests.post(
                f"{self.chromadb_base_url}/collections/{self.collection_name}/add",
                json={
                    "ids": ids,
                    "documents": documents,
                    "metadatas": metadatas
                },
                timeout=60
            )

            if response.status_code in [200, 201]:
                self.stats['vectorized_items'] += len(artworks)
                logger.info(f"✅ 成功向量化 {len(artworks)} 個藝術品")
            else:
                logger.warning(f"⚠️ ChromaDB添加響應: {response.status_code} - {response.text[:200]}")

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
                            a.period = $period,
                            a.source = $source,
                            a.description = $description,
                            a.updated_at = datetime()
                    """, **{
                        'id': artwork['id'],
                        'title': artwork['title'],
                        'date': artwork['date'],
                        'medium': artwork['medium'],
                        'culture': artwork['culture'],
                        'period': artwork['period'],
                        'source': artwork['source'],
                        'description': artwork['description'][:1000]
                    })

                    # 如果有藝術家，創建Artist節點和關係
                    if artwork['artist'] and artwork['artist'] != 'Unknown':
                        session.run("""
                            MERGE (artist:Artist {name: $artist_name})
                            WITH artist
                            MATCH (artwork:Artwork {id: $artwork_id})
                            MERGE (artist)-[:CREATED]->(artwork)
                        """, {
                            'artist_name': artwork['artist'],
                            'artwork_id': artwork['id']
                        })

                    # 如果有時期，創建Period節點和關係
                    if artwork['period']:
                        session.run("""
                            MERGE (period:Period {name: $period_name})
                            WITH period
                            MATCH (artwork:Artwork {id: $artwork_id})
                            MERGE (artwork)-[:BELONGS_TO_PERIOD]->(period)
                        """, {
                            'period_name': artwork['period'],
                            'artwork_id': artwork['id']
                        })

            self.stats['neo4j_items'] += len(artworks)
            logger.info(f"✅ 成功添加 {len(artworks)} 個藝術品到Neo4j")

        except Exception as e:
            logger.error(f"❌ Neo4j 添加失敗: {e}")
            self.stats['errors'].append(f"Neo4j 添加失敗: {e}")

    def process_data_file(self, file_path: Path):
        """處理單個資料文件"""
        logger.info(f"📂 處理文件: {file_path.name}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 提取藝術品列表
            artworks_raw = []
            if isinstance(data, list):
                artworks_raw = data
            elif isinstance(data, dict):
                if 'data' in data:
                    artworks_raw = data['data']
                elif 'items' in data:
                    artworks_raw = data['items']
                elif 'artworks' in data:
                    artworks_raw = data['artworks']
                else:
                    artworks_raw = [data]

            if not artworks_raw:
                logger.warning(f"⚠️ 文件中沒有找到資料: {file_path.name}")
                return

            # 標準化資料
            source = file_path.stem
            artworks = []
            for item in artworks_raw:
                try:
                    normalized = self.normalize_artwork_data(item, source)
                    artworks.append(normalized)
                except Exception as e:
                    logger.warning(f"標準化資料時出錯: {e}")
                    continue

            self.stats['total_items'] += len(artworks)
            logger.info(f"  提取了 {len(artworks)} 個藝術品")

            # 批量處理（每次50個）
            batch_size = 50
            for i in range(0, len(artworks), batch_size):
                batch = artworks[i:i + batch_size]

                # 添加到ChromaDB
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

        logger.info("\n" + "=" * 60)
        logger.info("📊 向量資料庫整合摘要")
        logger.info("=" * 60)
        logger.info(f"處理文件: {self.stats['processed_files']}/{self.stats['total_files']}")
        logger.info(f"總藝術品數: {self.stats['total_items']}")
        logger.info(f"向量化項目: {self.stats['vectorized_items']}")
        logger.info(f"Neo4j項目: {self.stats['neo4j_items']}")
        logger.info(f"耗時: {duration:.1f} 秒")

        if self.stats['errors']:
            logger.info(f"\n⚠️ 錯誤 ({len(self.stats['errors'])}):")
            for error in self.stats['errors'][:10]:
                logger.info(f"  - {error}")

        logger.info("=" * 60 + "\n")

    def run(self, hours=24):
        """執行整合流程"""
        logger.info("🚀 開始向量資料庫整合...")

        try:
            # 連接服務
            self.connect_services()

            # 加載資料文件
            files = self.load_recent_data_files(hours)

            if not files:
                logger.warning("⚠️ 沒有找到需要處理的資料文件")
                return

            # 處理每個文件
            for file_path in files:
                self.process_data_file(file_path)

            # 打印摘要
            self.print_summary()

            logger.info("✅ 向量資料庫整合完成！")

        except Exception as e:
            logger.error(f"❌ 整合失敗: {e}")
            raise
        finally:
            # 關閉連接
            if self.neo4j_driver:
                self.neo4j_driver.close()

def main():
    """主程序"""
    import argparse

    parser = argparse.ArgumentParser(description='向量資料庫整合工具')
    parser.add_argument(
        '--hours',
        type=int,
        default=24,
        help='處理最近N小時內的資料文件（預設：24）'
    )

    args = parser.parse_args()

    integrator = VectorDBIntegrator()
    integrator.run(hours=args.hours)

if __name__ == '__main__':
    main()
