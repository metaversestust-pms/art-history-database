#!/usr/bin/env python3
"""
將文藝復興和巴洛克時期資料處理並導入到RAG系統
包含Neo4j知識圖譜和ChromaDB向量資料庫
"""

import json
import logging
from pathlib import Path
from datetime import datetime
import sys

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RenaissanceBaroqueRAGProcessor:
    """文藝復興和巴洛克時期資料RAG處理器"""

    def __init__(self, data_dir="./renaissance_baroque_data"):
        self.data_dir = Path(data_dir)

        # Neo4j配置
        self.neo4j_uri = "bolt://localhost:7687"
        self.neo4j_user = "neo4j"
        self.neo4j_password = "arthistory123"

        # ChromaDB配置
        self.chromadb_host = "localhost"
        self.chromadb_port = 8001
        self.collection_name = "renaissance_baroque_art"

    def load_data(self):
        """載入爬取的資料"""
        logger.info("📁 載入文藝復興和巴洛克時期資料...")

        combined_file = self.data_dir / "combined_renaissance_baroque.json"

        if not combined_file.exists():
            logger.error(f"❌ 找不到合併資料檔案: {combined_file}")
            return None

        with open(combined_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        logger.info(f"✅ 成功載入 {len(data)} 件藝術作品")
        return data

    def process_to_neo4j(self, artworks):
        """處理並導入資料到Neo4j"""
        logger.info("\n" + "="*60)
        logger.info("步驟1: 處理並導入資料到Neo4j知識圖譜")
        logger.info("="*60)

        try:
            from neo4j import GraphDatabase

            logger.info(f"連接到Neo4j: {self.neo4j_uri}")
            driver = GraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_user, self.neo4j_password)
            )

            with driver.session() as session:
                # 創建約束和索引
                logger.info("創建約束和索引...")
                session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (a:Artwork) REQUIRE a.id IS UNIQUE")
                session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (p:Artist) REQUIRE p.id IS UNIQUE")
                session.run("CREATE INDEX IF NOT EXISTS FOR (a:Artwork) ON (a.title)")
                session.run("CREATE INDEX IF NOT EXISTS FOR (a:Artwork) ON (a.classification)")
                session.run("CREATE INDEX IF NOT EXISTS FOR (a:Artwork) ON (a.period)")

                # 處理每件作品
                logger.info(f"開始導入 {len(artworks)} 件作品...")

                successful = 0
                failed = 0

                for i, artwork in enumerate(artworks, 1):
                    try:
                        # 提取作品資訊
                        artwork_id = artwork.get('id', 0)
                        title = self._clean_string(artwork.get('title', 'Untitled'))
                        dated = self._clean_string(artwork.get('dated', ''))
                        medium = self._clean_string(artwork.get('medium', ''))
                        classification = self._clean_string(artwork.get('classification', ''))
                        culture = self._clean_string(artwork.get('culture', ''))
                        period = self._clean_string(artwork.get('period', ''))

                        # 判斷時期
                        if not period:
                            period = self._determine_period(artwork)

                        description = self._clean_string(artwork.get('description', ''))

                        # 創建作品節點
                        session.run("""
                            MERGE (a:Artwork {id: $id})
                            SET a.title = $title,
                                a.dated = $dated,
                                a.medium = $medium,
                                a.classification = $classification,
                                a.culture = $culture,
                                a.period = $period,
                                a.description = $description,
                                a.source = 'Harvard Art Museums',
                                a.updated_at = datetime()
                        """, {
                            'id': artwork_id,
                            'title': title,
                            'dated': dated,
                            'medium': medium,
                            'classification': classification,
                            'culture': culture,
                            'period': period,
                            'description': description
                        })

                        # 處理藝術家關係
                        if 'people' in artwork and artwork['people']:
                            for person in artwork['people']:
                                person_id = person.get('personid')
                                person_name = self._clean_string(person.get('name', 'Unknown'))
                                role = person.get('role', '')

                                if person_id and role in ['Artist', 'Creator', 'Maker']:
                                    # 創建藝術家節點
                                    session.run("""
                                        MERGE (p:Artist {id: $person_id})
                                        SET p.name = $name,
                                            p.updated_at = datetime()
                                    """, {
                                        'person_id': person_id,
                                        'name': person_name
                                    })

                                    # 創建關係
                                    session.run("""
                                        MATCH (a:Artwork {id: $artwork_id}), (p:Artist {id: $person_id})
                                        MERGE (p)-[:CREATED]->(a)
                                    """, {
                                        'artwork_id': artwork_id,
                                        'person_id': person_id
                                    })

                        successful += 1

                        if i % 100 == 0:
                            logger.info(f"  進度: {i}/{len(artworks)} ({successful}成功, {failed}失敗)")

                    except Exception as e:
                        failed += 1
                        logger.warning(f"  作品 {artwork.get('id')} 處理失敗: {str(e)[:100]}")

                logger.info(f"\n✅ Neo4j導入完成！")
                logger.info(f"   成功: {successful} 件作品")
                logger.info(f"   失敗: {failed} 件作品")

                # 顯示統計資訊
                self._show_neo4j_stats(session)

            driver.close()
            return {'successful': successful, 'failed': failed}

        except ImportError:
            logger.error("❌ 找不到neo4j模組，請安裝: pip install neo4j")
            return None
        except Exception as e:
            logger.error(f"❌ Neo4j處理失敗: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _determine_period(self, artwork):
        """根據作品資訊判斷時期"""
        # 檢查標題、描述等是否包含時期關鍵詞
        text = f"{artwork.get('title', '')} {artwork.get('description', '')} {artwork.get('culture', '')}".lower()

        if any(keyword in text for keyword in ['renaissance', 'raphael', 'leonardo', 'michelangelo', 'titian']):
            return 'Renaissance'
        elif any(keyword in text for keyword in ['baroque', 'caravaggio', 'rembrandt', 'rubens', 'velazquez']):
            return 'Baroque'

        # 根據日期判斷
        dated = artwork.get('dated', '')
        if dated:
            # 嘗試提取年份
            import re
            years = re.findall(r'\d{4}', dated)
            if years:
                year = int(years[0])
                if 1300 <= year <= 1600:
                    return 'Renaissance'
                elif 1600 < year <= 1750:
                    return 'Baroque'

        return 'Unknown'

    def _show_neo4j_stats(self, session):
        """顯示Neo4j統計資訊"""
        try:
            logger.info("\n📊 Neo4j資料統計:")

            # 統計作品數量
            result = session.run("MATCH (a:Artwork) RETURN count(a) as count")
            artwork_count = result.single()['count']
            logger.info(f"   總作品數: {artwork_count}")

            # 統計藝術家數量
            result = session.run("MATCH (p:Artist) RETURN count(p) as count")
            artist_count = result.single()['count']
            logger.info(f"   總藝術家數: {artist_count}")

            # 統計關係數量
            result = session.run("MATCH ()-[r:CREATED]->() RETURN count(r) as count")
            relation_count = result.single()['count']
            logger.info(f"   創作關係數: {relation_count}")

            # 統計各時期作品
            result = session.run("""
                MATCH (a:Artwork)
                WHERE a.period IS NOT NULL
                RETURN a.period as period, count(a) as count
                ORDER BY count DESC
            """)
            logger.info("\n   各時期作品分布:")
            for record in result:
                logger.info(f"     {record['period']}: {record['count']}")

        except Exception as e:
            logger.warning(f"無法獲取統計資訊: {e}")

    def process_to_chromadb(self, artworks):
        """處理並導入資料到ChromaDB"""
        logger.info("\n" + "="*60)
        logger.info("步驟2: 處理並導入資料到ChromaDB向量資料庫")
        logger.info("="*60)

        try:
            import chromadb
            from chromadb.config import Settings

            logger.info(f"連接到ChromaDB: {self.chromadb_host}:{self.chromadb_port}")

            # 連接到ChromaDB
            client = chromadb.HttpClient(
                host=self.chromadb_host,
                port=self.chromadb_port,
                settings=Settings(anonymized_telemetry=False)
            )

            # 創建或獲取集合
            try:
                # 嘗試刪除舊集合
                try:
                    client.delete_collection(self.collection_name)
                    logger.info(f"刪除舊集合: {self.collection_name}")
                except:
                    pass

                collection = client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "Renaissance and Baroque Art Collection"}
                )
                logger.info(f"創建新集合: {self.collection_name}")
            except:
                collection = client.get_collection(self.collection_name)
                logger.info(f"使用現有集合: {self.collection_name}")

            # 準備資料
            logger.info(f"準備處理 {len(artworks)} 件作品...")

            documents = []
            metadatas = []
            ids = []

            for artwork in artworks:
                artwork_id = str(artwork.get('id', ''))
                title = artwork.get('title', 'Untitled')
                description = artwork.get('description', '')
                medium = artwork.get('medium', '')
                culture = artwork.get('culture', '')
                classification = artwork.get('classification', '')
                dated = artwork.get('dated', '')
                period = self._determine_period(artwork)

                # 提取藝術家名稱
                artist_names = []
                if 'people' in artwork and artwork['people']:
                    for person in artwork['people']:
                        if person.get('role') in ['Artist', 'Creator', 'Maker']:
                            artist_names.append(person.get('name', ''))

                artist_str = ', '.join(artist_names) if artist_names else 'Unknown'

                # 組合文本用於嵌入
                text_parts = [
                    f"Title: {title}",
                    f"Period: {period}",
                    f"Artist: {artist_str}",
                    f"Dated: {dated}" if dated else "",
                    f"Medium: {medium}" if medium else "",
                    f"Culture: {culture}" if culture else "",
                    f"Classification: {classification}" if classification else "",
                    f"Description: {description}" if description else ""
                ]

                text = " | ".join([part for part in text_parts if part])
                text = text[:2000]  # 限制長度

                documents.append(text)
                metadatas.append({
                    'title': title[:200],
                    'artist': artist_str[:200],
                    'period': period,
                    'dated': dated[:100],
                    'medium': medium[:200],
                    'culture': culture[:100],
                    'classification': classification[:100],
                    'source': 'Harvard Art Museums'
                })
                ids.append(f"renaissance_baroque_{artwork_id}")

            # 批量添加到ChromaDB
            logger.info(f"添加 {len(documents)} 個文檔到ChromaDB...")

            batch_size = 100
            successful = 0

            for i in range(0, len(documents), batch_size):
                batch_docs = documents[i:i+batch_size]
                batch_metas = metadatas[i:i+batch_size]
                batch_ids = ids[i:i+batch_size]

                try:
                    collection.add(
                        documents=batch_docs,
                        metadatas=batch_metas,
                        ids=batch_ids
                    )
                    successful += len(batch_docs)
                    logger.info(f"  進度: {min(i+batch_size, len(documents))}/{len(documents)}")
                except Exception as e:
                    logger.warning(f"  批次 {i} 添加失敗: {str(e)[:100]}")

            # 檢查集合統計
            count = collection.count()

            logger.info(f"\n✅ ChromaDB導入完成！")
            logger.info(f"   集合名稱: {self.collection_name}")
            logger.info(f"   文檔數量: {count}")
            logger.info(f"   成功添加: {successful} 個文檔")

            return {
                'collection_name': self.collection_name,
                'documents_added': successful,
                'total_count': count
            }

        except ImportError:
            logger.error("❌ 找不到chromadb模組，請安裝: pip install chromadb")
            return None
        except Exception as e:
            logger.error(f"❌ ChromaDB處理失敗: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _clean_string(self, text):
        """清理字串"""
        if not text:
            return ''
        # 移除特殊字元，限制長度
        text = str(text).replace('\n', ' ').replace('\r', ' ')
        text = ' '.join(text.split())  # 移除多餘空白
        return text[:500]

    def run_complete_process(self):
        """執行完整的處理流程"""
        logger.info("🚀 開始處理文藝復興和巴洛克時期資料到RAG系統")
        logger.info("="*60)

        start_time = datetime.now()
        results = {}

        # 載入資料
        artworks = self.load_data()
        if not artworks:
            logger.error("❌ 載入資料失敗，終止流程")
            return None

        # 處理到Neo4j
        neo4j_result = self.process_to_neo4j(artworks)
        results['neo4j'] = neo4j_result

        # 處理到ChromaDB
        chromadb_result = self.process_to_chromadb(artworks)
        results['chromadb'] = chromadb_result

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info("\n" + "="*60)
        logger.info("🎉 處理流程完成！")
        logger.info("="*60)
        logger.info(f"總耗時: {duration:.2f} 秒")
        logger.info(f"處理作品數: {len(artworks)}")

        if neo4j_result:
            logger.info(f"Neo4j: {neo4j_result.get('successful', 0)} 件作品成功導入")

        if chromadb_result:
            logger.info(f"ChromaDB: {chromadb_result.get('documents_added', 0)} 個文檔成功導入")

        # 保存結果摘要
        summary = {
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': duration,
            'total_artworks': len(artworks),
            'results': results
        }

        summary_file = self.data_dir / "rag_processing_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        logger.info(f"\n💾 處理摘要已保存到: {summary_file}")

        return results

def main():
    """主函數"""
    print("\n🎨 文藝復興和巴洛克時期資料RAG處理器")
    print("="*60)
    print("此程式將執行以下步驟：")
    print("  1. 載入文藝復興和巴洛克時期爬取的資料")
    print("  2. 處理並導入到Neo4j知識圖譜")
    print("  3. 處理並導入到ChromaDB向量資料庫")
    print("="*60)

    # 詢問配置
    data_dir = input("\n資料目錄（按Enter使用默認: ./renaissance_baroque_data）: ").strip()
    if not data_dir:
        data_dir = "./renaissance_baroque_data"

    confirm = input(f"\n確認開始處理？(y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ 已取消")
        return

    # 創建處理器並執行
    processor = RenaissanceBaroqueRAGProcessor(data_dir=data_dir)
    results = processor.run_complete_process()

    if results:
        print("\n"+"="*60)
        print("✅ 文藝復興和巴洛克時期資料已成功處理並導入RAG系統！")
        print("="*60)
        print("\n💡 下一步：")
        print("  1. 在Neo4j瀏覽器中查看知識圖譜: http://localhost:7474")
        print("  2. 在OpenWebUI中測試RAG模型: http://localhost:8080")
        print("  3. 提問關於文藝復興和巴洛克時期的藝術史問題")
        print("\n範例問題：")
        print("  - 請介紹文藝復興時期的代表藝術家")
        print("  - 巴洛克時期有哪些重要作品？")
        print("  - Caravaggio和Rembrandt的作品有什麼特色？")

if __name__ == "__main__":
    main()
