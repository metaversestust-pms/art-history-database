#!/usr/bin/env python3
"""
Neo4j Graph RAG 服務器
提供基於知識圖譜的 RAG 查詢服務
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase
import logging
import time
from datetime import datetime
import sys
import os
import requests
import json
import math
import re
from collections import Counter, defaultdict

# 添加 langchain-rag 目錄到路徑以導入翻譯器
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'langchain-rag'))
try:
    from multilingual_query_translator import MultilingualQueryTranslator
    TRANSLATOR_AVAILABLE = True
except ImportError:
    TRANSLATOR_AVAILABLE = False
    logger.warning("⚠️ 多語言翻譯器未找到，將只支援英文查詢")

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Neo4j Graph RAG API", version="1.0.0")

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Neo4j 連接配置
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "arthistory123"

# ChromaDB 配置
CHROMA_BASE_URL = "http://localhost:8001"
CHROMA_TENANT = "default_tenant"
CHROMA_DATABASE = "default_database"
CHROMA_COLLECTION = "art_history_collection"
OLLAMA_URL = "http://localhost:11434"
EMBEDDING_MODEL = "nomic-embed-text"

class QueryRequest(BaseModel):
    query: str
    strategy: str = "graph_only"
    top_k: int = 5
    include_sources: bool = True

class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    strategy_used: str
    confidence_score: float
    processing_time: float

class Neo4jGraphRAG:
    """Neo4j Graph RAG 查詢引擎"""

    def __init__(self):
        self.driver = None
        self.translator = None
        self.chroma_url = f"{CHROMA_BASE_URL}/api/v2/tenants/{CHROMA_TENANT}/databases/{CHROMA_DATABASE}"
        self.collection_id = None
        self.connect()
        self.init_translator()
        self.init_chromadb()

    def connect(self):
        """連接到 Neo4j"""
        try:
            self.driver = GraphDatabase.driver(
                NEO4J_URI,
                auth=(NEO4J_USER, NEO4J_PASSWORD)
            )
            # 測試連接
            with self.driver.session() as session:
                session.run("RETURN 1")
            logger.info("✅ Neo4j 連接成功")
        except Exception as e:
            logger.error(f"❌ Neo4j 連接失敗: {e}")
            raise

    def init_translator(self):
        """初始化多語言翻譯器"""
        if TRANSLATOR_AVAILABLE:
            try:
                self.translator = MultilingualQueryTranslator()
                logger.info("✅ 多語言翻譯器初始化成功")
            except Exception as e:
                logger.warning(f"⚠️ 翻譯器初始化失敗: {e}")
                self.translator = None
        else:
            logger.warning("⚠️ 多語言翻譯器不可用")

    def init_chromadb(self):
        """初始化 ChromaDB 連接"""
        try:
            # 獲取集合列表
            response = requests.get(f"{self.chroma_url}/collections")
            if response.status_code == 200:
                collections = response.json()
                # 查找目標集合
                for collection in collections:
                    if collection.get('name') == CHROMA_COLLECTION:
                        self.collection_id = collection.get('id')
                        logger.info(f"✅ ChromaDB 連接成功 (集合: {CHROMA_COLLECTION}, ID: {self.collection_id})")
                        return
                logger.warning(f"⚠️ 未找到集合 '{CHROMA_COLLECTION}'")
            else:
                logger.warning(f"⚠️ ChromaDB 連接失敗: HTTP {response.status_code}")
        except Exception as e:
            logger.warning(f"⚠️ ChromaDB 初始化失敗: {e}")

    def close(self):
        """關閉連接"""
        if self.driver:
            self.driver.close()

    def tokenize(self, text: str) -> List[str]:
        """文本分詞和預處理"""
        if not text:
            return []

        # 轉換為小寫
        text = text.lower()

        # 移除標點符號，保留字母、數字和空格
        text = re.sub(r'[^\w\s]', ' ', text)

        # 分詞
        tokens = text.split()

        # 停用詞列表（簡化版）
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'is', 'was', 'are', 'were', 'been', 'be',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'
        }

        # 過濾停用詞和短詞
        tokens = [t for t in tokens if len(t) > 2 and t not in stop_words]

        return tokens

    def calculate_bm25_score(self, query_terms: List[str], document: str,
                            doc_freq: Dict[str, int], total_docs: int,
                            avg_doc_length: float, k1: float = 1.5, b: float = 0.75) -> float:
        """
        計算 BM25 分數

        Args:
            query_terms: 查詢詞列表
            document: 文檔文本
            doc_freq: 詞項文檔頻率 {term: count}
            total_docs: 總文檔數
            avg_doc_length: 平均文檔長度
            k1: BM25 參數（通常 1.2-2.0）
            b: BM25 參數（通常 0.75）

        Returns:
            BM25 分數
        """
        if not document or not query_terms:
            return 0.0

        # 文檔分詞
        doc_tokens = self.tokenize(document)
        doc_length = len(doc_tokens)

        if doc_length == 0:
            return 0.0

        # 計算詞頻
        term_freq = Counter(doc_tokens)

        # 計算 BM25 分數
        score = 0.0
        for term in query_terms:
            if term not in term_freq:
                continue

            # 詞頻
            tf = term_freq[term]

            # 文檔頻率（包含該詞的文檔數）
            df = doc_freq.get(term, 0)

            # IDF 計算：log((N - df + 0.5) / (df + 0.5) + 1)
            idf = math.log((total_docs - df + 0.5) / (df + 0.5) + 1.0)

            # BM25 公式
            numerator = tf * (k1 + 1)
            denominator = tf + k1 * (1 - b + b * (doc_length / avg_doc_length))

            score += idf * (numerator / denominator)

        return score

    def calculate_entity_importance(self, entity: Dict) -> float:
        """
        計算實體重要性分數

        Args:
            entity: 實體數據（藝術家或作品）

        Returns:
            重要性分數 [0, 1]
        """
        importance = 0.0

        # 藝術家作品數量（最多加 0.3 分）
        if 'artwork_count' in entity:
            count_score = min(0.3, entity['artwork_count'] / 50 * 0.3)
            importance += count_score

        # 館藏地位（加 0.4 分）
        prestigious_museums = {
            'louvre', 'metropolitan', 'vatican', 'uffizi', 'prado',
            'british museum', 'hermitage', 'rijksmuseum', 'moma'
        }
        museum = entity.get('museum') or ''
        if museum and any(pm in museum.lower() for pm in prestigious_museums):
            importance += 0.4

        # 描述長度（描述越詳細，通常越重要，最多加 0.3 分）
        description = entity.get('description', '')
        if description:
            desc_score = min(0.3, len(description) / 500 * 0.3)
            importance += desc_score

        return min(1.0, importance)

    def extract_keywords(self, query: str) -> List[str]:
        """從查詢中提取關鍵詞（支持短語匹配）"""
        # 藝術史相關關鍵詞
        art_keywords = [
            'renaissance', 'baroque', 'impressionism', 'modern', 'medieval',
            'artist', 'artwork', 'painting', 'sculpture', 'museum',
            'period', 'style', 'movement', 'culture'
        ]

        keywords = []
        query_lower = query.lower()

        # 1. 提取引號中的內容（最高優先級）
        quoted = re.findall(r'"([^"]*)"', query)
        keywords.extend(quoted)

        # 2. 識別常見的藝術作品短語（2-3個連續大寫單詞）
        # 例如：Mona Lisa, The Last Supper, School of Athens
        words = query.split()
        i = 0
        while i < len(words):
            # 尋找連續的大寫單詞（2-4個）
            phrase_words = []
            j = i
            while j < len(words) and j < i + 4:
                word = words[j].strip('.,;!?')
                # 檢查是否是大寫單詞或常見的小寫連接詞
                if word and (word[0].isupper() or word.lower() in ['of', 'the', 'a', 'an', 'in', 'de', 'da', 'von']):
                    phrase_words.append(word)
                    j += 1
                else:
                    break

            # 如果找到2個或更多連續單詞，作為短語
            if len(phrase_words) >= 2:
                phrase = ' '.join(phrase_words)
                keywords.append(phrase)
                i = j
            else:
                i += 1

        # 3. 提取藝術史關鍵詞
        for keyword in art_keywords:
            if keyword in query_lower:
                keywords.append(keyword.title())

        # 4. 提取單個大寫單詞（如果還沒有在短語中）
        added_phrases = set(' '.join(keywords).split())
        for word in words:
            clean_word = word.strip('.,;!?')
            if clean_word and clean_word[0].isupper() and len(clean_word) > 3:
                if clean_word not in added_phrases:
                    keywords.append(clean_word)

        # 去重並返回
        seen = set()
        unique_keywords = []
        for kw in keywords:
            kw_lower = kw.lower()
            if kw_lower not in seen:
                seen.add(kw_lower)
                unique_keywords.append(kw)

        return unique_keywords[:7]  # 返回前7個關鍵詞（增加以支持短語）

    def generate_embedding(self, text: str) -> List[float]:
        """生成文本 embedding"""
        try:
            response = requests.post(
                f"{OLLAMA_URL}/api/embeddings",
                json={"model": EMBEDDING_MODEL, "prompt": text},
                timeout=30
            )
            if response.status_code == 200:
                return response.json().get('embedding')
            else:
                logger.error(f"生成 embedding 失敗: HTTP {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"生成 embedding 失敗: {e}")
            return None

    def query_chromadb(self, query_embedding: List[float], top_k: int = 5) -> List[Dict]:
        """查詢 ChromaDB"""
        if not self.collection_id:
            logger.warning("ChromaDB 集合未初始化")
            return []

        try:
            response = requests.post(
                f"{self.chroma_url}/collections/{self.collection_id}/query",
                json={
                    "query_embeddings": [query_embedding],
                    "n_results": top_k,
                    "include": ["metadatas", "documents", "distances"]
                },
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                results = []

                # ChromaDB v2 返回格式
                if 'ids' in data and len(data['ids']) > 0:
                    ids = data['ids'][0]
                    metadatas = data.get('metadatas', [[]])[0]
                    documents = data.get('documents', [[]])[0]
                    distances = data.get('distances', [[]])[0]

                    for i in range(len(ids)):
                        # 改進的相似度分數計算
                        # ChromaDB 返回 L2 squared distance，先轉換為 L2 distance
                        distance = distances[i] if i < len(distances) else 0
                        l2_distance = math.sqrt(distance) if distance > 0 else 0

                        # 使用指數衰減公式，scaling_factor 基於觀察到的距離範圍調整
                        # 對於 768 維向量 with nomic-embed-text，L2 距離通常在 0-30 範圍內
                        # scaling_factor = 30 使得 distance=16 時 score≈0.59
                        scaling_factor = 30.0
                        similarity_score = math.exp(-l2_distance / scaling_factor)

                        result = {
                            'id': ids[i],
                            'metadata': metadatas[i] if i < len(metadatas) else {},
                            'document': documents[i] if i < len(documents) else '',
                            'distance': distance,
                            'l2_distance': l2_distance,
                            'score': similarity_score
                        }
                        results.append(result)

                return results
            else:
                logger.error(f"ChromaDB 查詢失敗: HTTP {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"ChromaDB 查詢失敗: {e}")
            return []

    def search_artists(self, keywords: List[str], limit: int = 5) -> List[Dict]:
        """搜索藝術家"""
        with self.driver.session() as session:
            results = []

            # 精確匹配
            for keyword in keywords:
                query = """
                MATCH (artist:Artist)
                WHERE artist.name CONTAINS $keyword
                OPTIONAL MATCH (artist)-[:CREATED]->(artwork:Artwork)
                RETURN artist.name as name,
                       artist.nationality as nationality,
                       artist.birth_year as birth_year,
                       artist.death_year as death_year,
                       count(artwork) as artwork_count
                LIMIT $limit
                """
                result = session.run(query, keyword=keyword, limit=limit)
                results.extend([dict(record) for record in result])

            return results[:limit]

    def search_artworks(self, keywords: List[str], limit: int = 5) -> List[Dict]:
        """搜索藝術作品"""
        with self.driver.session() as session:
            results = []

            for keyword in keywords:
                query = """
                MATCH (artwork:Artwork)
                WHERE artwork.title CONTAINS $keyword
                   OR artwork.description CONTAINS $keyword
                OPTIONAL MATCH (artist:Artist)-[:CREATED]->(artwork)
                OPTIONAL MATCH (artwork)-[:FROM_PERIOD]->(period:Period)
                OPTIONAL MATCH (artwork)-[:HOUSED_IN]->(museum:Museum)
                RETURN artwork.title as title,
                       artwork.date as date,
                       artwork.description as description,
                       artist.name as artist,
                       period.name as period,
                       museum.name as museum
                LIMIT $limit
                """
                result = session.run(query, keyword=keyword, limit=limit)
                results.extend([dict(record) for record in result])

            return results[:limit]

    def search_by_period(self, keywords: List[str], limit: int = 5) -> List[Dict]:
        """按時期搜索"""
        with self.driver.session() as session:
            results = []

            for keyword in keywords:
                query = """
                MATCH (period:Period)
                WHERE period.name CONTAINS $keyword
                MATCH (artwork:Artwork)-[:FROM_PERIOD]->(period)
                OPTIONAL MATCH (artist:Artist)-[:CREATED]->(artwork)
                RETURN period.name as period,
                       artwork.title as title,
                       artist.name as artist,
                       artwork.date as date
                LIMIT $limit
                """
                result = session.run(query, keyword=keyword, limit=limit)
                results.extend([dict(record) for record in result])

            return results[:limit]

    def search_relationships(self, entity: str, limit: int = 5) -> List[Dict]:
        """搜索實體關係"""
        with self.driver.session() as session:
            query = """
            MATCH (n)
            WHERE n.name CONTAINS $entity OR n.title CONTAINS $entity
            MATCH path = (n)-[r]-(connected)
            RETURN n.name as entity_name,
                   n.title as entity_title,
                   type(r) as relationship,
                   connected.name as connected_name,
                   connected.title as connected_title,
                   labels(connected) as connected_type
            LIMIT $limit
            """
            result = session.run(query, entity=entity, limit=limit)
            return [dict(record) for record in result]

    def get_statistics(self) -> Dict:
        """獲取知識圖譜統計"""
        with self.driver.session() as session:
            stats = {}

            # 節點統計
            result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] as type, count(n) as count
                ORDER BY count DESC
            """)
            stats['nodes'] = [dict(record) for record in result]

            # 關係統計
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as type, count(r) as count
                ORDER BY count DESC
            """)
            stats['relationships'] = [dict(record) for record in result]

            return stats

    def query(self, query_text: str, strategy: str = "graph_only", top_k: int = 5) -> Dict[str, Any]:
        """執行 RAG 查詢（支援多種策略）"""
        start_time = time.time()

        # 多語言翻譯
        original_query = query_text
        if self.translator:
            try:
                translation_result = self.translator.translate_query(query_text)
                query_text = translation_result.get('translated_query', query_text)
                if query_text != original_query:
                    logger.info(f"🌍 查詢翻譯: '{original_query}' → '{query_text}'")
                    logger.info(f"🔑 找到的術語: {translation_result.get('found_terms', [])}")
            except Exception as e:
                logger.warning(f"⚠️ 翻譯失敗，使用原始查詢: {e}")

        # 根據策略執行查詢
        if strategy == "vector_only":
            return self.query_vector_only(query_text, top_k, start_time)
        elif strategy == "hybrid_balanced":
            return self.query_hybrid(query_text, top_k, start_time)
        else:  # graph_only
            return self.query_graph_only(query_text, top_k, start_time)

    def query_graph_only(self, query_text: str, top_k: int, start_time: float) -> Dict[str, Any]:
        """純圖譜查詢（使用 BM25 排序）"""
        # 提取關鍵詞
        keywords = self.extract_keywords(query_text)
        logger.info(f"提取的關鍵詞: {keywords}")

        # 搜索不同類型的實體
        artists = self.search_artists(keywords, limit=top_k)
        artworks = self.search_artworks(keywords, limit=top_k * 2)  # 獲取更多結果用於排序
        periods = self.search_by_period(keywords, limit=top_k)

        # 如果有明確的實體，搜索關係
        relationships = []
        if keywords:
            relationships = self.search_relationships(keywords[0], limit=top_k)

        # 整合結果
        all_results = {
            "artists": artists,
            "artworks": artworks,
            "periods": periods,
            "relationships": relationships
        }

        # 使用 BM25 對 artworks 排序
        query_terms = self.tokenize(query_text)

        if artworks and query_terms:
            # 計算文檔統計
            all_documents = [
                f"{aw.get('title', '')} {aw.get('description', '')} {aw.get('artist', '')}"
                for aw in artworks
            ]

            total_docs = len(all_documents)
            doc_lengths = [len(self.tokenize(doc)) for doc in all_documents]
            avg_doc_length = sum(doc_lengths) / total_docs if total_docs > 0 else 1.0

            # 計算詞項文檔頻率
            doc_freq = defaultdict(int)
            for doc in all_documents:
                doc_tokens = set(self.tokenize(doc))
                for token in doc_tokens:
                    doc_freq[token] += 1

            # 為每個 artwork 計算 BM25 分數和實體重要性
            artwork_scores = []
            for artwork in artworks:
                document = f"{artwork.get('title', '')} {artwork.get('description', '')} {artwork.get('artist', '')}"

                # BM25 分數（權重 0.7）
                bm25_score = self.calculate_bm25_score(
                    query_terms, document, dict(doc_freq), total_docs, avg_doc_length
                )

                # 實體重要性分數（權重 0.3）
                importance = self.calculate_entity_importance(artwork)

                # 綜合分數
                final_score = bm25_score * 0.7 + importance * 0.3

                artwork_scores.append((artwork, final_score))

            # 按分數排序
            artwork_scores.sort(key=lambda x: x[1], reverse=True)
            artworks = [aw for aw, score in artwork_scores[:top_k]]

            # 動態歸一化分數
            sources = []
            if artwork_scores:
                # 獲取最大和最小分數用於歸一化
                max_score = artwork_scores[0][1] if artwork_scores else 1.0
                min_score = artwork_scores[min(len(artwork_scores)-1, top_k-1)][1] if len(artwork_scores) > 0 else 0.0
                score_range = max_score - min_score if max_score > min_score else 1.0

                for artwork, score in artwork_scores[:top_k]:
                    # Min-Max 歸一化到 [0.4, 0.95] 範圍
                    # 保持分數的相對差異，同時確保合理的分數範圍
                    if score_range > 0:
                        normalized_score = 0.4 + (score - min_score) / score_range * 0.55
                    else:
                        # 所有分數相同時，使用中等分數
                        normalized_score = 0.7

                    sources.append({
                        "title": artwork.get("title", "Unknown"),
                        "artist": artwork.get("artist", "Unknown"),
                        "date": artwork.get("date", "Unknown"),
                        "period": artwork.get("period", "Unknown"),
                        "score": normalized_score,
                        "bm25_score": score,
                        "raw_score": score
                    })
        else:
            # 沒有結果時的後備處理
            sources = []
            for artwork in artworks[:top_k]:
                sources.append({
                    "title": artwork.get("title", "Unknown"),
                    "artist": artwork.get("artist", "Unknown"),
                    "date": artwork.get("date", "Unknown"),
                    "period": artwork.get("period", "Unknown"),
                    "score": 0.7  # 後備固定分數
                })

        # 生成回答
        answer = self.generate_answer(query_text, all_results, keywords)

        processing_time = time.time() - start_time

        return {
            "answer": answer,
            "sources": sources,
            "strategy_used": "graph_only",
            "confidence_score": self.calculate_confidence(all_results),
            "processing_time": processing_time,
            "raw_results": all_results
        }

    def query_vector_only(self, query_text: str, top_k: int, start_time: float) -> Dict[str, Any]:
        """純向量查詢"""
        # 生成查詢 embedding
        query_embedding = self.generate_embedding(query_text)
        if not query_embedding:
            return {
                "answer": "無法生成查詢向量，請稍後再試。",
                "sources": [],
                "strategy_used": "vector_only",
                "confidence_score": 0.0,
                "processing_time": time.time() - start_time
            }

        # 查詢 ChromaDB
        vector_results = self.query_chromadb(query_embedding, top_k)

        # 準備來源資料
        sources = []
        for result in vector_results:
            metadata = result.get('metadata', {})
            sources.append({
                "title": metadata.get("title", "Unknown"),
                "artist": metadata.get("artist", "Unknown"),
                "date": metadata.get("date", "Unknown"),
                "period": metadata.get("period", "Unknown"),
                "score": result.get("score", 0.0)
            })

        # 生成回答
        answer = self.generate_vector_answer(query_text, vector_results)

        processing_time = time.time() - start_time

        return {
            "answer": answer,
            "sources": sources,
            "strategy_used": "vector_only",
            "confidence_score": self.calculate_vector_confidence(vector_results),
            "processing_time": processing_time
        }

    def query_hybrid(self, query_text: str, top_k: int, start_time: float) -> Dict[str, Any]:
        """混合查詢（圖譜 + 向量，改進的分數融合）"""
        # 同時執行圖譜和向量查詢
        keywords = self.extract_keywords(query_text)
        query_terms = self.tokenize(query_text)

        # 圖譜查詢
        graph_artworks = self.search_artworks(keywords, limit=top_k * 2)

        # 向量查詢
        query_embedding = self.generate_embedding(query_text)
        vector_results = []
        if query_embedding:
            vector_results = self.query_chromadb(query_embedding, top_k * 2)

        # 計算圖譜結果的 BM25 分數
        graph_scores = {}
        raw_scores_list = []

        if graph_artworks and query_terms:
            all_documents = [
                f"{aw.get('title', '')} {aw.get('description', '')} {aw.get('artist', '')}"
                for aw in graph_artworks
            ]

            total_docs = len(all_documents)
            doc_lengths = [len(self.tokenize(doc)) for doc in all_documents]
            avg_doc_length = sum(doc_lengths) / total_docs if total_docs > 0 else 1.0

            # 計算詞項文檔頻率
            doc_freq = defaultdict(int)
            for doc in all_documents:
                doc_tokens = set(self.tokenize(doc))
                for token in doc_tokens:
                    doc_freq[token] += 1

            # 第一遍：計算所有原始分數
            temp_scores = []
            for artwork in graph_artworks:
                # BM25 分數
                document = f"{artwork.get('title', '')} {artwork.get('description', '')} {artwork.get('artist', '')}"
                bm25_score = self.calculate_bm25_score(
                    query_terms, document, dict(doc_freq), total_docs, avg_doc_length
                )

                # 實體重要性
                importance = self.calculate_entity_importance(artwork)

                # 綜合分數
                raw_score = bm25_score * 0.7 + importance * 0.3
                temp_scores.append((artwork, raw_score, bm25_score))
                raw_scores_list.append(raw_score)

            # 獲取分數範圍用於歸一化
            if raw_scores_list:
                max_raw = max(raw_scores_list)
                min_raw = min(raw_scores_list)
                score_range = max_raw - min_raw if max_raw > min_raw else 1.0

                # 第二遍：歸一化分數
                for artwork, raw_score, bm25_score in temp_scores:
                    title = artwork.get("title", "Unknown")

                    # Min-Max 歸一化到 [0.3, 0.9] 範圍
                    if score_range > 0:
                        normalized_score = 0.3 + (raw_score - min_raw) / score_range * 0.6
                    else:
                        normalized_score = 0.6

                    graph_scores[title] = {
                        "artwork": artwork,
                        "score": normalized_score,
                        "raw_bm25": bm25_score,
                        "raw_score": raw_score
                    }

        # 合併結果
        combined_sources = {}

        # 添加圖譜結果
        for title, data in graph_scores.items():
            artwork = data["artwork"]
            graph_score = data["score"]

            combined_sources[title] = {
                "title": title,
                "artist": artwork.get("artist", "Unknown"),
                "date": artwork.get("date", "Unknown"),
                "period": artwork.get("period", "Unknown"),
                "museum": artwork.get("museum", ""),
                "description": artwork.get("description", ""),
                "graph_score": graph_score,
                "vector_score": 0.0,
                "score": graph_score * 0.7,  # 圖譜單獨結果權重 70%
                "source": "graph"
            }

        # 添加向量結果
        for result in vector_results:
            metadata = result.get('metadata', {})
            title = metadata.get("title", "Unknown")
            vector_score = result.get("score", 0.0)

            if title in combined_sources:
                # 雙重匹配：使用線性組合
                graph_s = combined_sources[title]["graph_score"]
                vector_s = vector_score

                # 線性加權組合：圖譜 60% + 向量 40% + 雙重匹配加成
                weighted_score = graph_s * 0.6 + vector_s * 0.4

                # 雙重匹配額外加成 15%
                combined_sources[title]["score"] = min(0.95, weighted_score * 1.15)
                combined_sources[title]["vector_score"] = vector_score
                combined_sources[title]["source"] = "hybrid"
            else:
                # 僅向量結果
                combined_sources[title] = {
                    "title": title,
                    "artist": metadata.get("artist", "Unknown"),
                    "date": metadata.get("date", "Unknown"),
                    "period": metadata.get("period", "Unknown"),
                    "museum": metadata.get("museum", ""),
                    "description": metadata.get("description", ""),
                    "graph_score": 0.0,
                    "vector_score": vector_score,
                    "score": vector_score * 0.85,  # 向量單獨結果權重 85%
                    "source": "vector"
                }

        # 排序並取前 top_k 個
        sources = sorted(combined_sources.values(), key=lambda x: x["score"], reverse=True)[:top_k]

        # 生成混合回答
        answer = self.generate_hybrid_answer(query_text, graph_artworks, vector_results, sources)

        processing_time = time.time() - start_time

        return {
            "answer": answer,
            "sources": sources,
            "strategy_used": "hybrid_balanced",
            "confidence_score": max([s["score"] for s in sources]) if sources else 0.0,
            "processing_time": processing_time
        }

    def generate_answer(self, query: str, results: Dict, keywords: List[str]) -> str:
        """基於圖譜結果生成回答"""
        answer_parts = []

        # 檢查是否有結果
        has_results = any(results.values())

        if not has_results:
            return f"""根據知識圖譜查詢，暫時沒有找到與「{query}」直接相關的藝術史資料。

建議：
- 嘗試使用更具體的藝術家名稱或作品名稱
- 使用藝術時期名稱（如 Renaissance、Baroque、Impressionism）
- 查詢特定的藝術運動或風格

目前知識圖譜包含：
- 1,135 件藝術作品
- 894 位藝術家
- 175 個博物館
- 8 個藝術時期"""

        # 藝術家資訊
        if results['artists']:
            answer_parts.append("## 🎨 相關藝術家\n")
            for artist in results['artists'][:3]:
                name = artist['name']
                nationality = artist.get('nationality', '未知')
                years = f"{artist.get('birth_year', '?')}-{artist.get('death_year', '?')}"
                count = artist.get('artwork_count', 0)
                answer_parts.append(f"- **{name}** ({nationality}, {years})\n  - 作品數量: {count}\n")

        # 藝術作品資訊
        if results['artworks']:
            answer_parts.append("\n## 🖼️ 相關作品\n")
            for artwork in results['artworks'][:3]:
                title = artwork['title']
                artist = artwork.get('artist', '未知藝術家')
                date = artwork.get('date', '未知年代')
                period = artwork.get('period', '')
                museum = artwork.get('museum', '')

                desc = f"- **{title}**\n"
                desc += f"  - 藝術家: {artist}\n"
                desc += f"  - 年代: {date}\n"
                if period:
                    desc += f"  - 時期: {period}\n"
                if museum:
                    desc += f"  - 收藏: {museum}\n"

                answer_parts.append(desc)

        # 時期資訊
        if results['periods']:
            answer_parts.append("\n## 📅 相關時期\n")
            period_groups = {}
            for item in results['periods']:
                period = item['period']
                if period not in period_groups:
                    period_groups[period] = []
                period_groups[period].append(item)

            for period, items in list(period_groups.items())[:3]:
                answer_parts.append(f"- **{period}**: {len(items)} 件作品\n")

        # 關係資訊
        if results['relationships']:
            answer_parts.append("\n## 🕸️ 相關連結\n")
            for rel in results['relationships'][:3]:
                entity = rel.get('entity_name') or rel.get('entity_title', 'Unknown')
                relation = rel.get('relationship', 'RELATED')
                connected = rel.get('connected_name') or rel.get('connected_title', 'Unknown')
                conn_type = rel.get('connected_type', ['Unknown'])[0]

                answer_parts.append(f"- {entity} → {relation} → {connected} ({conn_type})\n")

        # 添加總結
        if keywords:
            answer_parts.insert(0, f"基於知識圖譜的查詢結果（關鍵詞: {', '.join(keywords)}）：\n\n")

        return "".join(answer_parts)

    def calculate_confidence(self, results: Dict) -> float:
        """計算信心分數"""
        total_results = sum(len(v) for v in results.values())
        if total_results == 0:
            return 0.0
        elif total_results < 3:
            return 0.5
        elif total_results < 10:
            return 0.75
        else:
            return 0.95

    def calculate_vector_confidence(self, vector_results: List[Dict]) -> float:
        """計算向量檢索信心分數"""
        if not vector_results:
            return 0.0

        scores = [r.get('score', 0.0) for r in vector_results]
        if not scores:
            return 0.0

        # 使用加權平均：最高分數權重 0.6，平均分數權重 0.4
        max_score = max(scores)
        avg_score = sum(scores) / len(scores)
        confidence = max_score * 0.6 + avg_score * 0.4

        # 根據結果數量調整信心度
        if len(vector_results) >= 3:
            confidence = min(0.95, confidence * 1.1)  # 多個結果時提升信心
        elif len(vector_results) == 1:
            confidence = confidence * 0.8  # 只有一個結果時降低信心

        return min(0.95, max(0.0, confidence))

    def generate_vector_answer(self, query: str, vector_results: List[Dict]) -> str:
        """基於向量檢索結果生成回答"""
        if not vector_results:
            return f"根據向量檢索，暫時沒有找到與「{query}」相關的藝術史資料。"

        answer_parts = [f"基於向量語義檢索的結果：\n\n## 🎨 相關作品\n"]

        for i, result in enumerate(vector_results[:3], 1):
            metadata = result.get('metadata', {})
            document = result.get('document', '')
            score = result.get('score', 0.0)

            answer_parts.append(f"{i}. **{metadata.get('title', 'Unknown')}**\n")
            answer_parts.append(f"   - 藝術家: {metadata.get('artist', 'Unknown')}\n")
            answer_parts.append(f"   - 年代: {metadata.get('date', 'Unknown')}\n")
            answer_parts.append(f"   - 時期: {metadata.get('period', 'Unknown')}\n")
            answer_parts.append(f"   - 相似度: {score:.2%}\n")

            # 添加文檔摘要（前200字）
            if document:
                snippet = document[:200] + "..." if len(document) > 200 else document
                answer_parts.append(f"   - 描述: {snippet}\n")

            answer_parts.append("\n")

        return "".join(answer_parts)

    def generate_hybrid_answer(self, query: str, graph_results: List[Dict],
                               vector_results: List[Dict], combined_sources: List[Dict]) -> str:
        """基於混合檢索結果生成回答"""
        if not combined_sources:
            return f"根據混合檢索，暫時沒有找到與「{query}」相關的藝術史資料。"

        answer_parts = [f"基於知識圖譜和向量語義的混合檢索結果：\n\n## 🎨 相關作品\n"]

        for i, source in enumerate(combined_sources[:5], 1):
            answer_parts.append(f"{i}. **{source['title']}**\n")
            answer_parts.append(f"   - 藝術家: {source['artist']}\n")
            answer_parts.append(f"   - 年代: {source['date']}\n")
            answer_parts.append(f"   - 時期: {source['period']}\n")
            answer_parts.append(f"   - 綜合分數: {source['score']:.2%}\n")
            answer_parts.append(f"   - 來源: {source.get('source', 'unknown')}\n\n")

        # 添加檢索統計
        graph_count = sum(1 for s in combined_sources if s.get('source') in ['graph', 'hybrid'])
        vector_count = sum(1 for s in combined_sources if s.get('source') in ['vector', 'hybrid'])
        hybrid_count = sum(1 for s in combined_sources if s.get('source') == 'hybrid')

        answer_parts.append(f"\n**檢索統計**:\n")
        answer_parts.append(f"- 圖譜匹配: {graph_count} 件\n")
        answer_parts.append(f"- 向量匹配: {vector_count} 件\n")
        answer_parts.append(f"- 雙重匹配: {hybrid_count} 件\n")

        return "".join(answer_parts)

# 初始化 Graph RAG
graph_rag = None

@app.on_event("startup")
async def startup_event():
    """啟動時初始化"""
    global graph_rag
    try:
        graph_rag = Neo4jGraphRAG()
        logger.info("✅ Neo4j Graph RAG 服務啟動成功")
    except Exception as e:
        logger.error(f"❌ 啟動失敗: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """關閉時清理"""
    if graph_rag:
        graph_rag.close()
    logger.info("🛑 Neo4j Graph RAG 服務已關閉")

@app.get("/")
async def root():
    """根路徑"""
    return {
        "service": "Neo4j Graph RAG API",
        "version": "1.0.0",
        "status": "running",
        "neo4j_uri": NEO4J_URI
    }

@app.get("/health")
async def health_check():
    """健康檢查"""
    if graph_rag and graph_rag.driver:
        return {"status": "healthy", "neo4j": "connected"}
    return {"status": "unhealthy", "neo4j": "disconnected"}

@app.get("/system/strategies")
async def get_strategies():
    """獲取可用策略"""
    return {
        "strategies": [
            {
                "name": "graph_only",
                "display_name": "Graph RAG",
                "description": "純知識圖譜檢索，探索實體關係",
                "enabled": True
            },
            {
                "name": "vector_only",
                "display_name": "Vector RAG",
                "description": "純向量語義檢索，基於內容相似度",
                "enabled": graph_rag.collection_id is not None if graph_rag else False
            },
            {
                "name": "hybrid_balanced",
                "display_name": "Hybrid RAG",
                "description": "混合向量和圖譜檢索，綜合多種信號",
                "enabled": graph_rag.collection_id is not None if graph_rag else False
            }
        ]
    }

@app.get("/stats")
async def get_stats():
    """獲取知識圖譜統計"""
    if not graph_rag:
        raise HTTPException(status_code=503, detail="Graph RAG not initialized")

    try:
        stats = graph_rag.get_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
async def query(request: QueryRequest):
    """執行 RAG 查詢（支援多種策略）"""
    if not graph_rag:
        raise HTTPException(status_code=503, detail="Graph RAG not initialized")

    try:
        logger.info(f"收到查詢: {request.query}, 策略: {request.strategy}")

        result = graph_rag.query(
            query_text=request.query,
            strategy=request.strategy,
            top_k=request.top_k
        )

        return result

    except Exception as e:
        logger.error(f"查詢失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008)
