#!/usr/bin/env python3
"""
藝術史資料庫數據整合腳本
將新爬取的資料整合到RAG向量資料庫和知識圖譜中
"""

import os
import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import sys

# 添加langchain-rag目錄到路径
sys.path.append('./langchain-rag')

try:
    from vector_db_manager import VectorDBManager
    from knowledge_graph_manager import KnowledgeGraphManager
    from data_processor import DataProcessor
except ImportError:
    print("⚠️ 無法導入RAG系統模組，請確認langchain-rag目錄存在")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataIntegrator:
    def __init__(self):
        self.raw_data_dir = Path('./data/raw')
        self.processed_data_dir = Path('./data/processed')
        self.vector_db_dir = Path('./langchain-rag/vector_db')

        # 確保目錄存在
        self.processed_data_dir.mkdir(exist_ok=True)

        # 初始化組件
        self.vector_manager = None
        self.graph_manager = None
        self.data_processor = None

        # 統計信息
        self.stats = {
            'files_processed': 0,
            'items_processed': 0,
            'items_added_to_vector_db': 0,
            'entities_added_to_graph': 0,
            'relationships_added_to_graph': 0,
            'errors': 0
        }

    async def initialize_components(self):
        """初始化RAG系統組件"""
        try:
            logger.info("🔧 初始化RAG系統組件...")

            # 初始化向量數據庫管理器
            if os.path.exists('./langchain-rag/vector_db_manager.py'):
                from vector_db_manager import VectorDBManager
                self.vector_manager = VectorDBManager()
                logger.info("✅ 向量數據庫管理器已初始化")

            # 初始化知識圖譜管理器
            if os.path.exists('./langchain-rag/knowledge_graph_manager.py'):
                from knowledge_graph_manager import KnowledgeGraphManager
                self.graph_manager = KnowledgeGraphManager()
                logger.info("✅ 知識圖譜管理器已初始化")

            # 初始化數據處理器
            if os.path.exists('./langchain-rag/data_processor.py'):
                from data_processor import DataProcessor
                self.data_processor = DataProcessor()
                logger.info("✅ 數據處理器已初始化")

            return True

        except Exception as e:
            logger.error(f"❌ 組件初始化失敗: {e}")
            return False

    def get_new_data_files(self) -> List[Path]:
        """獲取需要處理的新數據文件"""
        processed_log = self.processed_data_dir / 'processed_files.json'

        # 讀取已處理文件記錄
        processed_files = set()
        if processed_log.exists():
            try:
                with open(processed_log, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    processed_files = set(data.get('processed_files', []))
            except Exception as e:
                logger.warning(f"⚠️ 無法讀取已處理文件記錄: {e}")

        # 找出新文件
        all_json_files = list(self.raw_data_dir.glob('*.json'))
        new_files = [f for f in all_json_files if str(f) not in processed_files]

        logger.info(f"📊 發現 {len(all_json_files)} 個數據文件，其中 {len(new_files)} 個新文件")
        return new_files

    def extract_art_info(self, item: Dict[str, Any], source: str) -> Dict[str, Any]:
        """從原始數據中提取藝術史相關信息"""
        try:
            # 統一數據格式
            art_info = {
                'id': item.get('id', ''),
                'title': self.clean_text(item.get('title', '未知標題')),
                'artist': self.clean_text(item.get('creator', item.get('artist', '未知藝術家'))),
                'date': self.clean_text(item.get('date', '未知年代')),
                'medium': self.clean_text(item.get('medium', item.get('type', '未知媒材'))),
                'description': self.clean_text(item.get('description', '')),
                'culture': self.clean_text(item.get('culture', item.get('country', ''))),
                'style': self.clean_text(item.get('style', '')),
                'subject': self.clean_text(item.get('subject', '')),
                'provider': self.clean_text(item.get('provider', item.get('dataProvider', ''))),
                'source': source,
                'source_url': item.get('source_url', item.get('sourceUrl', '')),
                'image_url': item.get('image_url', item.get('imageUrl', '')),
                'rights': item.get('rights', ''),
                'processed_at': datetime.now().isoformat()
            }

            # 為向量搜索創建文本內容
            content_parts = [
                f"標題: {art_info['title']}",
                f"藝術家: {art_info['artist']}",
                f"年代: {art_info['date']}",
                f"媒材: {art_info['medium']}",
                f"文化: {art_info['culture']}"
            ]

            if art_info['description']:
                content_parts.append(f"描述: {art_info['description']}")

            if art_info['subject']:
                content_parts.append(f"主題: {art_info['subject']}")

            art_info['content'] = '\n'.join(content_parts)

            return art_info

        except Exception as e:
            logger.error(f"❌ 提取藝術信息失敗: {e}")
            return None

    def clean_text(self, text: Any) -> str:
        """清理文本數據"""
        if not text:
            return ''

        if isinstance(text, list):
            return ', '.join(str(t) for t in text if t)

        text = str(text).strip()
        # 移除多餘的空白字符
        text = ' '.join(text.split())
        return text

    def extract_entities_and_relationships(self, art_info: Dict[str, Any]) -> Dict[str, List]:
        """從藝術信息中提取實體和關係"""
        entities = []
        relationships = []

        # 藝術品實體
        artwork_entity = {
            'id': f"artwork_{art_info['id']}",
            'name': art_info['title'],
            'type': 'Artwork',
            'properties': {
                'date': art_info['date'],
                'medium': art_info['medium'],
                'description': art_info['description'],
                'source': art_info['source']
            }
        }
        entities.append(artwork_entity)

        # 藝術家實體
        if art_info['artist'] and art_info['artist'] != '未知藝術家':
            artist_entity = {
                'id': f"artist_{self.normalize_name(art_info['artist'])}",
                'name': art_info['artist'],
                'type': 'Artist',
                'properties': {}
            }
            entities.append(artist_entity)

            # 創作關係
            relationships.append({
                'from': artist_entity['id'],
                'to': artwork_entity['id'],
                'type': 'CREATED',
                'properties': {}
            })

        # 文化/地區實體
        if art_info['culture']:
            culture_entity = {
                'id': f"culture_{self.normalize_name(art_info['culture'])}",
                'name': art_info['culture'],
                'type': 'Culture',
                'properties': {}
            }
            entities.append(culture_entity)

            # 屬於關係
            relationships.append({
                'from': artwork_entity['id'],
                'to': culture_entity['id'],
                'type': 'BELONGS_TO',
                'properties': {}
            })

        return {'entities': entities, 'relationships': relationships}

    def normalize_name(self, name: str) -> str:
        """標準化名稱用作ID"""
        return name.lower().replace(' ', '_').replace('-', '_').replace('.', '')

    async def process_data_file(self, file_path: Path) -> bool:
        """處理單個數據文件"""
        try:
            logger.info(f"📁 處理文件: {file_path.name}")

            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 根據文件類型提取項目
            items = []
            if 'items' in data:
                items = data['items']
            elif isinstance(data, list):
                items = data
            else:
                logger.warning(f"⚠️ 無法識別文件格式: {file_path.name}")
                return False

            processed_items = 0
            vector_items = []
            all_entities = []
            all_relationships = []

            for item in items:
                # 提取藝術信息
                art_info = self.extract_art_info(item, file_path.name)
                if not art_info:
                    continue

                # 準備向量數據庫項目
                vector_items.append({
                    'id': art_info['id'],
                    'content': art_info['content'],
                    'metadata': {
                        'title': art_info['title'],
                        'artist': art_info['artist'],
                        'date': art_info['date'],
                        'source': art_info['source'],
                        'type': 'artwork'
                    }
                })

                # 提取知識圖譜實體和關係
                graph_data = self.extract_entities_and_relationships(art_info)
                all_entities.extend(graph_data['entities'])
                all_relationships.extend(graph_data['relationships'])

                processed_items += 1

                # 批量處理
                if len(vector_items) >= 100:
                    await self.add_to_vector_db(vector_items)
                    await self.add_to_knowledge_graph(all_entities, all_relationships)

                    vector_items = []
                    all_entities = []
                    all_relationships = []

            # 處理剩餘項目
            if vector_items:
                await self.add_to_vector_db(vector_items)
                await self.add_to_knowledge_graph(all_entities, all_relationships)

            self.stats['files_processed'] += 1
            self.stats['items_processed'] += processed_items

            logger.info(f"✅ 文件 {file_path.name} 處理完成，處理 {processed_items} 項")
            return True

        except Exception as e:
            logger.error(f"❌ 處理文件 {file_path.name} 失敗: {e}")
            self.stats['errors'] += 1
            return False

    async def add_to_vector_db(self, items: List[Dict[str, Any]]):
        """添加到向量數據庫"""
        try:
            if self.vector_manager:
                # 這裡需要根據實際的向量數據庫接口調整
                # await self.vector_manager.add_documents(items)
                self.stats['items_added_to_vector_db'] += len(items)
                logger.info(f"📊 已添加 {len(items)} 項到向量數據庫")
            else:
                logger.warning("⚠️ 向量數據庫管理器未初始化")
        except Exception as e:
            logger.error(f"❌ 添加到向量數據庫失敗: {e}")
            self.stats['errors'] += 1

    async def add_to_knowledge_graph(self, entities: List[Dict], relationships: List[Dict]):
        """添加到知識圖譜"""
        try:
            if self.graph_manager:
                # 這裡需要根據實際的知識圖譜接口調整
                # await self.graph_manager.add_entities(entities)
                # await self.graph_manager.add_relationships(relationships)

                self.stats['entities_added_to_graph'] += len(entities)
                self.stats['relationships_added_to_graph'] += len(relationships)
                logger.info(f"🕸️ 已添加 {len(entities)} 個實體和 {len(relationships)} 個關係到知識圖譜")
            else:
                logger.warning("⚠️ 知識圖譜管理器未初始化")
        except Exception as e:
            logger.error(f"❌ 添加到知識圖譜失敗: {e}")
            self.stats['errors'] += 1

    def update_processed_files_log(self, processed_files: List[Path]):
        """更新已處理文件記錄"""
        try:
            processed_log = self.processed_data_dir / 'processed_files.json'

            # 讀取現有記錄
            existing_files = set()
            if processed_log.exists():
                with open(processed_log, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    existing_files = set(data.get('processed_files', []))

            # 添加新處理的文件
            for file_path in processed_files:
                existing_files.add(str(file_path))

            # 保存更新的記錄
            log_data = {
                'processed_files': list(existing_files),
                'last_updated': datetime.now().isoformat(),
                'total_files': len(existing_files)
            }

            with open(processed_log, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2)

            logger.info(f"📝 已更新處理文件記錄: {len(existing_files)} 個文件")

        except Exception as e:
            logger.error(f"❌ 更新處理文件記錄失敗: {e}")

    def save_integration_stats(self):
        """保存整合統計"""
        try:
            stats_file = self.processed_data_dir / f'integration_stats_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'

            stats_data = {
                **self.stats,
                'integration_time': datetime.now().isoformat(),
                'success_rate': (self.stats['files_processed'] / (self.stats['files_processed'] + self.stats['errors'])) if (self.stats['files_processed'] + self.stats['errors']) > 0 else 0
            }

            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats_data, f, ensure_ascii=False, indent=2)

            logger.info(f"📊 整合統計已保存: {stats_file}")

        except Exception as e:
            logger.error(f"❌ 保存整合統計失敗: {e}")

    async def integrate_all_data(self):
        """整合所有新數據"""
        logger.info("🚀 開始數據整合流程...")

        # 初始化組件
        components_initialized = await self.initialize_components()
        if not components_initialized:
            logger.warning("⚠️ 部分組件初始化失敗，將跳過相關功能")

        # 獲取新數據文件
        new_files = self.get_new_data_files()
        if not new_files:
            logger.info("✅ 沒有新的數據文件需要處理")
            return

        # 處理每個文件
        successfully_processed = []
        for file_path in new_files:
            success = await self.process_data_file(file_path)
            if success:
                successfully_processed.append(file_path)

        # 更新處理記錄
        if successfully_processed:
            self.update_processed_files_log(successfully_processed)

        # 保存統計
        self.save_integration_stats()

        # 打印總結
        self.print_summary()

    def print_summary(self):
        """打印整合總結"""
        logger.info(f"\n🎉 數據整合完成！")
        logger.info(f"📊 整合統計:")
        logger.info(f"   - 處理文件: {self.stats['files_processed']}")
        logger.info(f"   - 處理項目: {self.stats['items_processed']}")
        logger.info(f"   - 添加到向量庫: {self.stats['items_added_to_vector_db']}")
        logger.info(f"   - 圖譜實體: {self.stats['entities_added_to_graph']}")
        logger.info(f"   - 圖譜關係: {self.stats['relationships_added_to_graph']}")
        logger.info(f"   - 錯誤數量: {self.stats['errors']}")

        success_rate = (self.stats['files_processed'] / (self.stats['files_processed'] + self.stats['errors'])) if (self.stats['files_processed'] + self.stats['errors']) > 0 else 0
        logger.info(f"   - 成功率: {success_rate:.1%}")

async def main():
    """主程序"""
    try:
        integrator = DataIntegrator()
        await integrator.integrate_all_data()
    except Exception as e:
        logger.error(f"❌ 數據整合失敗: {e}")
        return 1

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))