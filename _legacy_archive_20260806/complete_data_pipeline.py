#!/usr/bin/env python3
"""
完整的藝術史數據收集和處理流程
從Harvard API爬取數據 → 處理 → 導入Neo4j → 生成ChromaDB嵌入
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ArtHistoryDataPipeline:
    """藝術史數據完整處理流程"""

    def __init__(self, work_dir="./art_data_pipeline"):
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)

        self.harvard_dir = self.work_dir / "harvard_data"
        self.processed_dir = self.work_dir / "processed"
        self.neo4j_dir = self.work_dir / "neo4j_import"
        self.chromadb_dir = self.work_dir / "chromadb_data"

        for d in [self.harvard_dir, self.processed_dir, self.neo4j_dir, self.chromadb_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def step1_crawl_harvard_data(self, max_pages=3):
        """步驟1: 從Harvard API爬取新數據"""
        logger.info("=" * 60)
        logger.info("步驟1: 從Harvard Art Museums爬取數據")
        logger.info("=" * 60)

        try:
            # 切換到langchain-rag目錄
            original_dir = os.getcwd()
            langchain_rag_dir = Path(__file__).parent / "langchain-rag"

            if langchain_rag_dir.exists():
                os.chdir(langchain_rag_dir)
                sys.path.insert(0, str(langchain_rag_dir))

            from harvard_art_museums_crawler import HarvardArtMuseumsCrawler, HarvardCrawlerConfig

            # 配置爬蟲
            config = HarvardCrawlerConfig(
                api_key="cfe24845-aa4f-4c93-9d86-f6880440af5f",
                max_per_page=50,
                delay_seconds=0.5,
                output_dir=str(self.harvard_dir)
            )

            crawler = HarvardArtMuseumsCrawler(config)

            # 爬取數據
            logger.info(f"開始爬取數據，每種類型最多{max_pages}頁...")

            # 1. 爬取元數據
            logger.info("\n1.1 爬取元數據（分類、文化、媒材等）...")
            metadata = crawler.crawl_metadata()
            if metadata:
                crawler.save_data(metadata, 'harvard_metadata.json')

            # 2. 爬取作品數據
            logger.info(f"\n1.2 爬取作品數據（最多{max_pages}頁）...")
            objects = crawler.crawl_all_objects(max_pages=max_pages)
            if objects:
                crawler.save_data(objects, 'harvard_objects.json')
                logger.info(f"✅ 收集了 {len(objects)} 件藝術作品")

            # 3. 爬取人物數據
            logger.info(f"\n1.3 爬取人物數據（最多{max_pages}頁）...")
            people = crawler.crawl_all_people(max_pages=max_pages)
            if people:
                crawler.save_data(people, 'harvard_people.json')
                logger.info(f"✅ 收集了 {len(people)} 位藝術家/人物")

            # 4. 爬取展覽數據
            logger.info(f"\n1.4 爬取展覽數據（最多{max_pages}頁）...")
            exhibitions = crawler.crawl_all_exhibitions(max_pages=max_pages)
            if exhibitions:
                crawler.save_data(exhibitions, 'harvard_exhibitions.json')
                logger.info(f"✅ 收集了 {len(exhibitions)} 個展覽")

            # 保存摘要
            summary = {
                'timestamp': datetime.now().isoformat(),
                'api_calls_used': crawler.api_calls_count,
                'data_collected': {
                    'objects': len(objects) if objects else 0,
                    'people': len(people) if people else 0,
                    'exhibitions': len(exhibitions) if exhibitions else 0,
                    'metadata': len(metadata) if metadata else 0
                }
            }

            with open(self.harvard_dir / 'crawl_summary.json', 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)

            logger.info(f"\n✅ 步驟1完成！")
            logger.info(f"   API調用次數: {crawler.api_calls_count}")
            logger.info(f"   數據保存位置: {self.harvard_dir}")

            os.chdir(original_dir)
            return summary

        except Exception as e:
            logger.error(f"❌ 爬取數據失敗: {e}")
            import traceback
            traceback.print_exc()
            return None

    def step2_process_data_for_neo4j(self):
        """步驟2: 處理數據並生成Neo4j導入腳本"""
        logger.info("\n" + "=" * 60)
        logger.info("步驟2: 處理數據並生成Neo4j導入腳本")
        logger.info("=" * 60)

        try:
            # 讀取爬取的數據
            objects_file = self.harvard_dir / 'harvard_objects.json'
            people_file = self.harvard_dir / 'harvard_people.json'
            exhibitions_file = self.harvard_dir / 'harvard_exhibitions.json'
            metadata_file = self.harvard_dir / 'harvard_metadata.json'

            objects = []
            people = []
            exhibitions = []
            metadata = {}

            if objects_file.exists():
                with open(objects_file, 'r', encoding='utf-8') as f:
                    objects = json.load(f)

            if people_file.exists():
                with open(people_file, 'r', encoding='utf-8') as f:
                    people = json.load(f)

            if exhibitions_file.exists():
                with open(exhibitions_file, 'r', encoding='utf-8') as f:
                    exhibitions = json.load(f)

            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)

            logger.info(f"讀取數據完成:")
            logger.info(f"  - 作品: {len(objects)}")
            logger.info(f"  - 人物: {len(people)}")
            logger.info(f"  - 展覽: {len(exhibitions)}")

            # 生成Neo4j導入腳本
            cypher_script = self._generate_neo4j_import_script(objects, people, exhibitions, metadata)

            # 保存腳本
            script_file = self.neo4j_dir / 'import_harvard_data.cypher'
            with open(script_file, 'w', encoding='utf-8') as f:
                f.write(cypher_script)

            logger.info(f"✅ 步驟2完成！")
            logger.info(f"   Neo4j導入腳本: {script_file}")

            return {
                'objects_count': len(objects),
                'people_count': len(people),
                'exhibitions_count': len(exhibitions),
                'script_file': str(script_file)
            }

        except Exception as e:
            logger.error(f"❌ 處理數據失敗: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _generate_neo4j_import_script(self, objects, people, exhibitions, metadata):
        """生成Neo4j導入腳本"""
        logger.info("生成Neo4j Cypher導入腳本...")

        script = []
        script.append("// Harvard Art Museums數據導入腳本")
        script.append(f"// 生成時間: {datetime.now().isoformat()}")
        script.append(f"// 數據統計: {len(objects)}件作品, {len(people)}位人物, {len(exhibitions)}個展覽")
        script.append("")

        # 創建約束和索引
        script.append("// 創建約束和索引")
        script.append("CREATE CONSTRAINT IF NOT EXISTS FOR (a:Artwork) REQUIRE a.id IS UNIQUE;")
        script.append("CREATE CONSTRAINT IF NOT EXISTS FOR (p:Artist) REQUIRE p.id IS UNIQUE;")
        script.append("CREATE CONSTRAINT IF NOT EXISTS FOR (e:Exhibition) REQUIRE e.id IS UNIQUE;")
        script.append("")

        # 導入人物數據
        script.append("// 導入人物數據")
        for person in people[:100]:  # 限制數量避免腳本過大
            name = person.get('name', 'Unknown').replace("'", "\\'")
            person_id = person.get('id', 0)

            culture = person.get('culture', '').replace("'", "\\'")
            birth_place = person.get('birthplace', '').replace("'", "\\'")
            death_place = person.get('deathplace', '').replace("'", "\\'")

            cypher = f"""
MERGE (p:Artist {{id: {person_id}}})
SET p.name = '{name}',
    p.culture = '{culture}',
    p.birthplace = '{birth_place}',
    p.deathplace = '{death_place}',
    p.source = 'Harvard Art Museums';
"""
            script.append(cypher)

        script.append("")

        # 導入作品數據
        script.append("// 導入作品數據")
        for obj in objects[:200]:  # 限制數量
            title = obj.get('title', 'Untitled').replace("'", "\\'")[:200]
            obj_id = obj.get('id', 0)

            dated = obj.get('dated', '').replace("'", "\\'")
            medium = obj.get('medium', '').replace("'", "\\'")[:200]
            classification = obj.get('classification', '').replace("'", "\\'")
            culture = obj.get('culture', '').replace("'", "\\'")

            cypher = f"""
MERGE (a:Artwork {{id: {obj_id}}})
SET a.title = '{title}',
    a.dated = '{dated}',
    a.medium = '{medium}',
    a.classification = '{classification}',
    a.culture = '{culture}',
    a.source = 'Harvard Art Museums';
"""
            script.append(cypher)

            # 創建作者關係
            if 'people' in obj and obj['people']:
                for person in obj['people']:
                    if person.get('role') in ['Artist', 'Creator']:
                        person_id = person.get('personid')
                        if person_id:
                            script.append(f"""
MATCH (a:Artwork {{id: {obj_id}}}), (p:Artist {{id: {person_id}}})
MERGE (p)-[:CREATED]->(a);
""")

        script.append("")

        # 導入展覽數據
        script.append("// 導入展覽數據")
        for exhibition in exhibitions[:50]:  # 限制數量
            title = exhibition.get('title', 'Untitled Exhibition').replace("'", "\\'")[:200]
            ex_id = exhibition.get('id', 0)

            begin_date = exhibition.get('begindate', '')
            end_date = exhibition.get('enddate', '')

            cypher = f"""
MERGE (e:Exhibition {{id: {ex_id}}})
SET e.title = '{title}',
    e.begin_date = '{begin_date}',
    e.end_date = '{end_date}',
    e.source = 'Harvard Art Museums';
"""
            script.append(cypher)

        script.append("")
        script.append("// 導入完成")
        script.append(f"// 共導入: {min(len(people), 100)}位人物, {min(len(objects), 200)}件作品, {min(len(exhibitions), 50)}個展覽")

        return "\n".join(script)

    def step3_import_to_neo4j(self):
        """步驟3: 將數據導入Neo4j"""
        logger.info("\n" + "=" * 60)
        logger.info("步驟3: 導入數據到Neo4j")
        logger.info("=" * 60)

        try:
            from neo4j import GraphDatabase

            # Neo4j連接配置
            uri = "bolt://localhost:7687"
            user = "neo4j"
            password = "arthistory123"

            logger.info(f"連接到Neo4j: {uri}")
            driver = GraphDatabase.driver(uri, auth=(user, password))

            # 讀取Cypher腳本
            script_file = self.neo4j_dir / 'import_harvard_data.cypher'

            if not script_file.exists():
                logger.error(f"❌ 找不到導入腳本: {script_file}")
                return None

            with open(script_file, 'r', encoding='utf-8') as f:
                script_content = f.read()

            # 分割腳本並執行
            statements = [s.strip() for s in script_content.split(';') if s.strip() and not s.strip().startswith('//')]

            logger.info(f"準備執行 {len(statements)} 個Cypher語句...")

            successful = 0
            failed = 0

            with driver.session() as session:
                for i, statement in enumerate(statements, 1):
                    try:
                        if statement.strip():
                            session.run(statement)
                            successful += 1
                            if i % 20 == 0:
                                logger.info(f"  進度: {i}/{len(statements)} ({successful}成功, {failed}失敗)")
                    except Exception as e:
                        failed += 1
                        logger.warning(f"  語句執行失敗: {str(e)[:100]}")

            driver.close()

            logger.info(f"✅ 步驟3完成！")
            logger.info(f"   成功: {successful} 個語句")
            logger.info(f"   失敗: {failed} 個語句")

            # 檢查Neo4j數據統計
            self._check_neo4j_stats()

            return {
                'successful': successful,
                'failed': failed
            }

        except Exception as e:
            logger.error(f"❌ 導入Neo4j失敗: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _check_neo4j_stats(self):
        """檢查Neo4j數據統計"""
        try:
            from neo4j import GraphDatabase

            uri = "bolt://localhost:7687"
            user = "neo4j"
            password = "arthistory123"

            driver = GraphDatabase.driver(uri, auth=(user, password))

            with driver.session() as session:
                # 統計節點數量
                result = session.run("MATCH (n) RETURN labels(n)[0] as label, count(n) as count ORDER BY count DESC LIMIT 10")

                logger.info("\n📊 Neo4j數據統計:")
                for record in result:
                    logger.info(f"   {record['label']}: {record['count']} 個節點")

                # 統計總數
                result = session.run("MATCH (n) RETURN count(n) as total")
                total = result.single()['total']
                logger.info(f"   總節點數: {total}")

                # 統計關係
                result = session.run("MATCH ()-[r]->() RETURN type(r) as type, count(r) as count ORDER BY count DESC LIMIT 10")
                logger.info("\n🔗 關係統計:")
                for record in result:
                    logger.info(f"   {record['type']}: {record['count']} 個關係")

            driver.close()

        except Exception as e:
            logger.warning(f"無法獲取Neo4j統計: {e}")

    def step4_generate_chromadb_embeddings(self):
        """步驟4: 生成ChromaDB嵌入向量"""
        logger.info("\n" + "=" * 60)
        logger.info("步驟4: 生成ChromaDB嵌入向量")
        logger.info("=" * 60)

        try:
            import chromadb

            # 連接到ChromaDB
            client = chromadb.HttpClient(host='localhost', port=8001)

            # 創建或獲取集合
            collection_name = "harvard_art_collection"

            try:
                collection = client.get_collection(collection_name)
                logger.info(f"使用現有集合: {collection_name}")
            except:
                collection = client.create_collection(collection_name)
                logger.info(f"創建新集合: {collection_name}")

            # 讀取作品數據
            objects_file = self.harvard_dir / 'harvard_objects.json'

            if not objects_file.exists():
                logger.error(f"❌ 找不到作品數據: {objects_file}")
                return None

            with open(objects_file, 'r', encoding='utf-8') as f:
                objects = json.load(f)

            logger.info(f"準備處理 {len(objects)} 件作品...")

            # 準備數據
            documents = []
            metadatas = []
            ids = []

            for obj in objects[:500]:  # 限制數量
                obj_id = str(obj.get('id', ''))
                title = obj.get('title', 'Untitled')
                description = obj.get('description', '')
                medium = obj.get('medium', '')
                culture = obj.get('culture', '')
                classification = obj.get('classification', '')

                # 組合文本用於嵌入
                text = f"{title}. {description} Medium: {medium}. Culture: {culture}. Classification: {classification}"
                text = text[:1000]  # 限制長度

                documents.append(text)
                metadatas.append({
                    'title': title[:200],
                    'medium': medium[:100],
                    'culture': culture[:100],
                    'classification': classification[:100],
                    'source': 'Harvard Art Museums'
                })
                ids.append(f"harvard_{obj_id}")

            # 批量添加到ChromaDB
            logger.info(f"添加 {len(documents)} 個文檔到ChromaDB...")

            batch_size = 100
            for i in range(0, len(documents), batch_size):
                batch_docs = documents[i:i+batch_size]
                batch_metas = metadatas[i:i+batch_size]
                batch_ids = ids[i:i+batch_size]

                collection.add(
                    documents=batch_docs,
                    metadatas=batch_metas,
                    ids=batch_ids
                )
                logger.info(f"  進度: {min(i+batch_size, len(documents))}/{len(documents)}")

            # 檢查集合統計
            count = collection.count()

            logger.info(f"✅ 步驟4完成！")
            logger.info(f"   ChromaDB集合: {collection_name}")
            logger.info(f"   文檔數量: {count}")

            return {
                'collection_name': collection_name,
                'documents_added': len(documents),
                'total_count': count
            }

        except Exception as e:
            logger.error(f"❌ 生成ChromaDB嵌入失敗: {e}")
            import traceback
            traceback.print_exc()
            return None

    def run_complete_pipeline(self, max_pages=3):
        """運行完整的數據處理流程"""
        logger.info("🚀 開始運行完整的藝術史數據處理流程")
        logger.info("=" * 60)

        start_time = datetime.now()
        results = {
            'start_time': start_time.isoformat(),
            'steps': {}
        }

        # 步驟1: 爬取數據
        step1_result = self.step1_crawl_harvard_data(max_pages=max_pages)
        results['steps']['step1_crawl'] = step1_result

        if not step1_result:
            logger.error("❌ 步驟1失敗，終止流程")
            return results

        # 步驟2: 處理數據
        step2_result = self.step2_process_data_for_neo4j()
        results['steps']['step2_process'] = step2_result

        if not step2_result:
            logger.error("❌ 步驟2失敗，終止流程")
            return results

        # 步驟3: 導入Neo4j
        step3_result = self.step3_import_to_neo4j()
        results['steps']['step3_neo4j'] = step3_result

        # 步驟4: 生成ChromaDB嵌入
        step4_result = self.step4_generate_chromadb_embeddings()
        results['steps']['step4_chromadb'] = step4_result

        end_time = datetime.now()
        results['end_time'] = end_time.isoformat()
        results['duration_seconds'] = (end_time - start_time).total_seconds()

        # 保存完整結果
        results_file = self.work_dir / 'pipeline_results.json'
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        logger.info("\n" + "=" * 60)
        logger.info("🎉 完整流程執行完成！")
        logger.info("=" * 60)
        logger.info(f"總耗時: {results['duration_seconds']:.2f} 秒")
        logger.info(f"結果文件: {results_file}")
        logger.info("\n📊 流程總結:")

        if step1_result:
            logger.info(f"  ✅ 步驟1 - 爬取數據: {step1_result.get('data_collected', {})}")
        if step2_result:
            logger.info(f"  ✅ 步驟2 - 處理數據: {step2_result.get('objects_count', 0)} 件作品")
        if step3_result:
            logger.info(f"  ✅ 步驟3 - Neo4j導入: {step3_result.get('successful', 0)} 個語句成功")
        if step4_result:
            logger.info(f"  ✅ 步驟4 - ChromaDB嵌入: {step4_result.get('documents_added', 0)} 個文檔")

        return results


def main():
    """主函數"""
    print("🎨 藝術史數據完整處理流程")
    print("=" * 60)
    print("此腳本將執行以下步驟:")
    print("  1. 從Harvard Art Museums API爬取新數據")
    print("  2. 處理數據並生成Neo4j導入腳本")
    print("  3. 將數據導入Neo4j知識圖譜")
    print("  4. 生成ChromaDB向量嵌入")
    print("=" * 60)

    # 詢問用戶配置
    max_pages = input("\n每種數據類型爬取的最大頁數 (建議3-5): ").strip() or "3"
    max_pages = int(max_pages)

    work_dir = input("工作目錄 (按Enter使用默認: ./art_data_pipeline): ").strip() or "./art_data_pipeline"

    confirm = input(f"\n確認開始執行流程? (y/n): ").strip().lower()

    if confirm != 'y':
        print("❌ 已取消")
        return

    # 創建並運行流程
    pipeline = ArtHistoryDataPipeline(work_dir=work_dir)
    results = pipeline.run_complete_pipeline(max_pages=max_pages)

    print("\n" + "=" * 60)
    print("✅ 流程執行完成！")
    print("=" * 60)
    print(f"📁 所有數據已保存到: {work_dir}/")
    print("\n💡 後續步驟:")
    print("  1. 在Neo4j瀏覽器中查看新數據: http://localhost:7474")
    print("  2. 在OpenWebUI中測試RAG模型: http://localhost:8080")
    print("  3. 選擇RAG模型提問藝術史問題")


if __name__ == "__main__":
    main()
