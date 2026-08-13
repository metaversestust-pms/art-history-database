#!/usr/bin/env python3
"""
多資料庫路由器
根據RAG策略自動選擇和融合多個資料源
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import time

from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RetrievalResult:
    """檢索結果數據類"""
    content: str
    score: float
    retrieval_method: str
    source_database: str
    source_collection: str
    source_type: str
    original_source: str
    metadata: Dict[str, Any]

class MultiDatabaseRouter:
    """多資料庫路由器"""

    def __init__(self):
        logger.info("🔀 初始化多資料庫路由器...")

        # Neo4j 配置
        self.neo4j_driver = GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "arthistory123")
        )

        # ChromaDB 配置
        self.chroma_url = "http://localhost:8001"
        self.chroma_collection = "art_history_collection"

        # 嵌入模型（用於向量搜索）
        self.embedding_model = SentenceTransformer('BAAI/bge-small-zh-v1.5')

        # 策略-資料源映射
        self.strategy_mapping = {
            "enhanced_rag": ["neo4j", "chromadb"],
            "vector_only": ["chromadb", "neo4j"],
            "graph_only": ["neo4j"],
            "hybrid_balanced": ["neo4j", "chromadb"],
            "advanced_rag": ["chromadb", "neo4j"],
            "agentic_rag": ["chromadb", "neo4j"],
            "self_rag": ["chromadb", "neo4j"],
            "naive_rag": ["chromadb"]
        }

        logger.info("✅ 多資料庫路由器初始化完成")

    def close(self):
        """關閉連接"""
        if self.neo4j_driver:
            self.neo4j_driver.close()

    def get_datasources(self, strategy: str) -> List[str]:
        """根據策略獲取資料源列表"""
        sources = self.strategy_mapping.get(strategy, ["neo4j"])
        logger.info(f"策略 '{strategy}' 使用資料源: {sources}")
        return sources

    async def query_neo4j_vector(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        """Neo4j 向量搜索"""
        results = []

        try:
            query_embedding = self.embedding_model.encode(query).tolist()

            with self.neo4j_driver.session() as session:
                # 向量搜索藝術家
                cypher_query = """
                    CALL db.index.vector.queryNodes('artist_name_embeddings', $top_k, $embedding)
                    YIELD node, score
                    RETURN node.name as name,
                           node.biography as biography,
                           'Artist' as type,
                           score
                """
                result = session.run(cypher_query, {'embedding': query_embedding, 'top_k': top_k})

                for record in result:
                    results.append(RetrievalResult(
                        content=f"{record['name']}: {record.get('biography', '')[:200]}",
                        score=record['score'],
                        retrieval_method="vector",
                        source_database="neo4j",
                        source_collection="graph_database",
                        source_type=record['type'],
                        original_source="WikiArt / Met Museum",
                        metadata={
                            "name": record['name'],
                            "type": record['type']
                        }
                    ))

                # 向量搜索作品
                cypher_query = """
                    CALL db.index.vector.queryNodes('artwork_title_embeddings', $top_k, $embedding)
                    YIELD node, score
                    RETURN node.title as title,
                           node.description as description,
                           'Artwork' as type,
                           score
                """
                result = session.run(cypher_query, {'embedding': query_embedding, 'top_k': top_k})

                for record in result:
                    results.append(RetrievalResult(
                        content=f"{record['title']}: {record.get('description', '')[:200]}",
                        score=record['score'],
                        retrieval_method="vector",
                        source_database="neo4j",
                        source_collection="graph_database",
                        source_type=record['type'],
                        original_source="WikiArt / Met Museum",
                        metadata={
                            "title": record['title'],
                            "type": record['type']
                        }
                    ))

        except Exception as e:
            logger.error(f"Neo4j 向量搜索失敗: {e}")

        return results

    async def query_neo4j_fulltext(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        """Neo4j 全文搜索"""
        results = []

        try:
            with self.neo4j_driver.session() as session:
                # 全文搜索藝術家
                cypher_query = """
                    CALL db.index.fulltext.queryNodes('artist_fulltext', $query)
                    YIELD node, score
                    RETURN node.name as name,
                           node.biography as biography,
                           'Artist' as type,
                           score
                    ORDER BY score DESC
                    LIMIT $top_k
                """
                result = session.run(cypher_query, {'query': query, 'top_k': top_k})

                for record in result:
                    results.append(RetrievalResult(
                        content=f"{record['name']}: {record.get('biography', '')[:200]}",
                        score=record['score'],
                        retrieval_method="fulltext",
                        source_database="neo4j",
                        source_collection="graph_database",
                        source_type=record['type'],
                        original_source="WikiArt / Met Museum",
                        metadata={
                            "name": record['name'],
                            "type": record['type']
                        }
                    ))

        except Exception as e:
            logger.error(f"Neo4j 全文搜索失敗: {e}")

        return results

    async def query_chromadb(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        """ChromaDB 向量搜索"""
        results = []

        try:
            # 生成查詢向量
            query_embedding = self.embedding_model.encode(query).tolist()

            # 查詢ChromaDB
            response = requests.post(
                f"{self.chroma_url}/api/v2/tenants/default_tenant/databases/default_database/collections/{self.chroma_collection}/query",
                json={
                    "query_embeddings": [query_embedding],
                    "n_results": top_k,
                    "include": ["metadatas", "documents", "distances"]
                }
            )

            if response.status_code == 200:
                data = response.json()

                for i, (doc, metadata, distance) in enumerate(zip(
                    data.get('documents', [[]])[0],
                    data.get('metadatas', [[]])[0],
                    data.get('distances', [[]])[0]
                )):
                    # 轉換距離為相似度分數
                    score = 1 / (1 + distance)

                    results.append(RetrievalResult(
                        content=doc[:300],
                        score=score,
                        retrieval_method="vector",
                        source_database="chromadb",
                        source_collection="art_history_collection",
                        source_type="artwork",
                        original_source=metadata.get('collection', 'Met Museum'),
                        metadata=metadata
                    ))

        except Exception as e:
            logger.error(f"ChromaDB 查詢失敗: {e}")

        return results

    async def route_query(
        self,
        query: str,
        strategy: str = "hybrid_balanced",
        top_k: int = 5
    ) -> List[RetrievalResult]:
        """
        路由查詢到適當的資料源

        Args:
            query: 查詢文本
            strategy: RAG策略
            top_k: 返回結果數量

        Returns:
            融合後的檢索結果列表
        """
        logger.info(f"🔀 路由查詢: {query} | 策略: {strategy}")

        start_time = time.time()
        sources = self.get_datasources(strategy)

        # 並行查詢多個資料源
        tasks = []

        if "neo4j" in sources:
            tasks.append(self.query_neo4j_vector(query, top_k))
            tasks.append(self.query_neo4j_fulltext(query, top_k))

        if "chromadb" in sources:
            tasks.append(self.query_chromadb(query, top_k))

        # 執行並行查詢
        all_results = await asyncio.gather(*tasks)

        # 合併結果
        merged_results = []
        for results in all_results:
            merged_results.extend(results)

        # 去重和排序
        unique_results = self._deduplicate(merged_results)
        sorted_results = sorted(unique_results, key=lambda x: x.score, reverse=True)[:top_k]

        retrieval_time = time.time() - start_time
        logger.info(f"✅ 檢索完成: {len(sorted_results)} 個結果 ({retrieval_time:.3f}秒)")

        # 統計資料源使用
        source_stats = {}
        for r in sorted_results:
            db = r.source_database
            source_stats[db] = source_stats.get(db, 0) + 1

        logger.info(f"📊 資料源分布: {source_stats}")

        return sorted_results

    def _deduplicate(self, results: List[RetrievalResult]) -> List[RetrievalResult]:
        """去重結果"""
        seen = set()
        unique = []

        for result in results:
            # 使用內容前50個字符作為去重鍵
            key = result.content[:50]
            if key not in seen:
                seen.add(key)
                unique.append(result)

        return unique

    def format_results_for_llm(self, results: List[RetrievalResult]) -> Dict[str, Any]:
        """格式化結果供LLM使用"""
        formatted = {
            "sources": [],
            "context": "",
            "metadata": {
                "total_results": len(results),
                "databases_used": list(set(r.source_database for r in results)),
                "source_distribution": {}
            }
        }

        # 統計各資料庫結果數
        for r in results:
            db = r.source_database
            formatted["metadata"]["source_distribution"][db] = \
                formatted["metadata"]["source_distribution"].get(db, 0) + 1

        # 構建sources和context
        for i, result in enumerate(results, 1):
            formatted["sources"].append({
                "rank": i,
                "content": result.content,
                "score": result.score,
                "retrieval_method": result.retrieval_method,
                "source_database": result.source_database,
                "source_collection": result.source_collection,
                "source_type": result.source_type,
                "original_source": result.original_source,
                "metadata": result.metadata
            })

            # 構建context文本
            formatted["context"] += f"\n[來源 {i}] ({result.source_database} > {result.original_source})\n"
            formatted["context"] += f"{result.content}\n"

        return formatted

# 測試代碼
async def test_router():
    """測試多資料庫路由器"""
    router = MultiDatabaseRouter()

    try:
        # 測試查詢
        test_queries = [
            ("達文西", "hybrid_balanced"),
            ("印象派", "vector_only"),
            ("文藝復興", "graph_only")
        ]

        for query, strategy in test_queries:
            logger.info(f"\n{'='*60}")
            logger.info(f"測試查詢: {query} | 策略: {strategy}")
            logger.info(f"{'='*60}")

            results = await router.route_query(query, strategy, top_k=5)

            # 顯示結果
            formatted = router.format_results_for_llm(results)

            logger.info(f"\n📊 結果統計:")
            logger.info(f"- 總結果數: {formatted['metadata']['total_results']}")
            logger.info(f"- 使用資料庫: {formatted['metadata']['databases_used']}")
            logger.info(f"- 資料源分布: {formatted['metadata']['source_distribution']}")

            logger.info(f"\n📚 前3個結果:")
            for source in formatted['sources'][:3]:
                logger.info(f"\n[{source['rank']}] 分數: {source['score']:.3f}")
                logger.info(f"來源: {source['source_database']} > {source['original_source']}")
                logger.info(f"方法: {source['retrieval_method']}")
                logger.info(f"內容: {source['content'][:100]}...")

    finally:
        router.close()

if __name__ == "__main__":
    asyncio.run(test_router())
