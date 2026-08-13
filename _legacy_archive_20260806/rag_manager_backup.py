#!/usr/bin/env python3
"""
統一 RAG 管理器服務 V2
提供多種 RAG 策略的統一接口，支援動態切換 LLM 模型和 RAG 策略
整合 Ollama 模型和 Neo4j/ChromaDB
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import httpx
from neo4j import GraphDatabase
import chromadb
from chromadb.config import Settings

# 導入多語言查詢翻譯器
from multilingual_query_translator import MultilingualQueryTranslator

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 創建 FastAPI 應用
app = FastAPI(
    title="Art History RAG Manager V2",
    description="統一 RAG 管理器 - 支援 42 種 RAG+LLM 組合",
    version="2.0.0"
)

# 添加 CORS 中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 配置加載 ====================

config_path = Path(__file__).parent / "rag_config.json"
with open(config_path, 'r', encoding='utf-8') as f:
    RAG_CONFIG = json.load(f)

# 環境變數配置
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "arthistory123")
CHROMADB_HOST = os.getenv("CHROMADB_HOST", "localhost")
CHROMADB_PORT = int(os.getenv("CHROMADB_PORT", "8001"))

# ==================== 請求/響應模型 ====================

class QueryRequest(BaseModel):
    """查詢請求模型"""
    query: str
    model_combination_id: str
    max_results: int = 5
    include_sources: bool = True
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None

class QueryResponse(BaseModel):
    """查詢響應模型"""
    answer: str
    sources: List[Dict[str, Any]]
    model_used: str
    rag_strategy: str
    retrieval_time_ms: float
    generation_time_ms: float
    metadata: Dict[str, Any]

class HealthResponse(BaseModel):
    """健康檢查響應"""
    status: str
    services: Dict[str, bool]
    timestamp: str

# ==================== 連接管理器 ====================

class ConnectionManager:
    """管理外部服務連接"""

    def __init__(self):
        self.neo4j_driver = None
        self.chroma_client = None
        self.http_client = httpx.AsyncClient(timeout=60.0)

    async def initialize(self):
        """初始化所有連接"""
        try:
            # Neo4j 連接
            logger.info(f"連接 Neo4j: {NEO4J_URI}")
            self.neo4j_driver = GraphDatabase.driver(
                NEO4J_URI,
                auth=(NEO4J_USER, NEO4J_PASSWORD)
            )
            # 測試連接
            self.neo4j_driver.verify_connectivity()
            logger.info("✅ Neo4j 連接成功")
        except Exception as e:
            logger.error(f"❌ Neo4j 連接失敗: {e}")
            self.neo4j_driver = None

        try:
            # ChromaDB 連接
            logger.info(f"連接 ChromaDB: {CHROMADB_HOST}:{CHROMADB_PORT}")
            self.chroma_client = chromadb.HttpClient(
                host=CHROMADB_HOST,
                port=CHROMADB_PORT
            )
            # 測試連接
            self.chroma_client.heartbeat()
            logger.info("✅ ChromaDB 連接成功")
        except Exception as e:
            logger.error(f"❌ ChromaDB 連接失敗: {e}")
            self.chroma_client = None

        # 測試 Ollama 連接
        try:
            logger.info(f"連接 Ollama: {OLLAMA_BASE_URL}")
            response = await self.http_client.get(f"{OLLAMA_BASE_URL}/api/tags")
            if response.status_code == 200:
                logger.info("✅ Ollama 連接成功")
            else:
                logger.error(f"❌ Ollama 連接失敗: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Ollama 連接失敗: {e}")

    async def close(self):
        """關閉所有連接"""
        if self.neo4j_driver:
            self.neo4j_driver.close()
        await self.http_client.aclose()

    def get_health_status(self) -> Dict[str, bool]:
        """獲取服務健康狀態"""
        status = {
            "neo4j": False,
            "chromadb": False,
            "ollama": False
        }

        # 檢查 Neo4j
        if self.neo4j_driver:
            try:
                self.neo4j_driver.verify_connectivity()
                status["neo4j"] = True
            except:
                pass

        # 檢查 ChromaDB
        if self.chroma_client:
            try:
                self.chroma_client.heartbeat()
                status["chromadb"] = True
            except:
                pass

        return status

# 全局連接管理器
conn_manager = ConnectionManager()

# 全局多語言翻譯器
query_translator = None

# ==================== RAG 策略實現 ====================

class RAGStrategy:
    """RAG 策略基類"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    async def retrieve(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """檢索相關文檔"""
        raise NotImplementedError

    async def generate(self, query: str, context: List[Dict[str, Any]],
                      model_id: str, temperature: float = 0.1,
                      max_tokens: int = 2048) -> str:
        """生成答案"""
        # 構建提示詞
        context_text = self._format_context(context)
        prompt = self._build_prompt(query, context_text)

        # 調用 Ollama
        try:
            response = await conn_manager.http_client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": model_id,
                    "prompt": prompt,
                    "temperature": temperature,
                    "stream": False
                },
                timeout=60.0
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                error_text = response.text
                logger.error(f"Ollama 生成失敗: {response.status_code}, 詳情: {error_text}")
                return f"抱歉，生成答案時發生錯誤（狀態碼: {response.status_code}）"
        except Exception as e:
            logger.error(f"調用 Ollama 失敗: {e}")
            return f"錯誤: {str(e)}"

    def _format_context(self, context: List[Dict[str, Any]]) -> str:
        """格式化上下文"""
        if not context:
            return "沒有找到相關資料。"

        formatted = []
        for i, doc in enumerate(context, 1):
            content = doc.get('content', doc.get('text', ''))
            source = doc.get('source', '未知來源')
            formatted.append(f"[文檔 {i}] 來源: {source}\n{content}")

        return "\n\n".join(formatted)

    def _build_prompt(self, query: str, context: str) -> str:
        """構建提示詞"""
        return f"""你是一位藝術史專家助手。請基於以下參考資料回答用戶的問題。

參考資料：
{context}

用戶問題：{query}

請提供準確、詳細的回答。如果參考資料中沒有相關信息，請誠實說明。
"""


class VectorOnlyRAG(RAGStrategy):
    """純向量檢索 RAG"""

    def __init__(self):
        super().__init__("Vector Only RAG", "使用向量數據庫進行語義檢索")

    async def retrieve(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """使用 ChromaDB 進行向量檢索"""
        if not conn_manager.chroma_client:
            logger.warning("ChromaDB 未連接，返回空結果")
            return []

        try:
            # 獲取或創建集合
            collection = conn_manager.chroma_client.get_or_create_collection(
                name="art_history"
            )

            # 執行查詢
            results = collection.query(
                query_texts=[query],
                n_results=max_results
            )

            # 格式化結果
            documents = []
            if results and results['documents']:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                    distance = results['distances'][0][i] if results['distances'] else 0

                    documents.append({
                        'content': doc,
                        'metadata': metadata,
                        'score': 1 - distance,  # 轉換為相似度分數
                        'source': metadata.get('source', 'ChromaDB')
                    })

            logger.info(f"向量檢索返回 {len(documents)} 個結果")
            return documents

        except Exception as e:
            logger.error(f"向量檢索失敗: {e}")
            return []


class GraphOnlyRAG(RAGStrategy):
    """純圖譜檢索 RAG"""

    def __init__(self):
        super().__init__("Graph Only RAG", "使用知識圖譜進行關係推理")

    async def retrieve(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """使用 Neo4j 進行圖譜檢索"""
        if not conn_manager.neo4j_driver:
            logger.warning("Neo4j 未連接，返回空結果")
            return []

        try:
            # 提取查詢中的關鍵實體（簡化版）
            entities = self._extract_entities(query)

            with conn_manager.neo4j_driver.session() as session:
                # 查詢藝術品和藝術家節點
                cypher_query = """
                MATCH (a:Artwork)
                WHERE toLower(a.title) CONTAINS toLower($search_text)
                   OR toLower(COALESCE(a.description, '')) CONTAINS toLower($search_text)
                   OR toLower(COALESCE(a.date, '')) CONTAINS toLower($search_text)
                OPTIONAL MATCH (a)-[r]-(related)
                RETURN a as n, collect({rel: type(r), node: related}) as relationships
                LIMIT $limit

                UNION

                MATCH (artist:Artist)
                WHERE toLower(artist.name) CONTAINS toLower($search_text)
                OPTIONAL MATCH (artist)-[r:CREATED]->(artwork:Artwork)
                RETURN artist as n, collect({rel: type(r), node: artwork}) as relationships
                LIMIT $limit
                """

                result = session.run(
                    cypher_query,
                    search_text=query,
                    limit=max_results
                )

                # 格式化結果
                documents = []
                for record in result:
                    node = record['n']
                    relationships = record['relationships']

                    # 構建文檔內容
                    content = self._format_graph_node(node, relationships)

                    documents.append({
                        'content': content,
                        'metadata': dict(node),
                        'score': 1.0,
                        'source': 'Neo4j Knowledge Graph'
                    })

                logger.info(f"圖譜檢索返回 {len(documents)} 個結果")
                return documents

        except Exception as e:
            logger.error(f"圖譜檢索失敗: {e}")
            return []

    def _extract_entities(self, query: str) -> List[str]:
        """簡單的實體提取（分詞）"""
        # 移除常見停用詞
        stop_words = {'的', '是', '有', '在', '和', '與', '或', '對', '為', '了', '個', '著', '嗎', '呢', '吧'}
        words = [w for w in query if len(w) > 1 and w not in stop_words]
        return words[:5]  # 限制最多5個實體

    def _format_graph_node(self, node, relationships) -> str:
        """格式化圖譜節點信息"""
        # 判斷節點類型並獲取名稱
        node_name = node.get('title') or node.get('name', '未知')
        content = f"實體: {node_name}\n"

        # 添加屬性
        for key, value in node.items():
            if key not in ['name', 'title'] and value:
                content += f"{key}: {value}\n"

        # 添加關係
        if relationships:
            content += "\n相關關係:\n"
            for rel in relationships[:5]:  # 限制關係數量
                if rel['node']:
                    rel_type = rel['rel']
                    rel_node = rel['node'].get('name', '未知')
                    content += f"  - {rel_type} -> {rel_node}\n"

        return content


class HybridBalancedRAG(RAGStrategy):
    """混合平衡 RAG - 結合向量和圖譜"""

    def __init__(self):
        super().__init__("Hybrid Balanced RAG", "平衡使用向量檢索和圖譜推理")
        self.vector_rag = VectorOnlyRAG()
        self.graph_rag = GraphOnlyRAG()

    async def retrieve(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """混合檢索"""
        # 從兩種策略各取一半
        vector_limit = max_results // 2
        graph_limit = max_results - vector_limit

        # 並行檢索
        vector_docs = await self.vector_rag.retrieve(query, vector_limit)
        graph_docs = await self.graph_rag.retrieve(query, graph_limit)

        # 合並結果
        all_docs = vector_docs + graph_docs

        logger.info(f"混合檢索返回 {len(all_docs)} 個結果 (向量: {len(vector_docs)}, 圖譜: {len(graph_docs)})")
        return all_docs


class AdvancedRAG(RAGStrategy):
    """高級 RAG - 多級檢索和重排序"""

    def __init__(self):
        super().__init__("Advanced RAG", "多級檢索、結果融合和重排序")
        self.vector_rag = VectorOnlyRAG()
        self.graph_rag = GraphOnlyRAG()

    async def retrieve(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """高級檢索流程"""
        # 第一階段：廣泛檢索
        vector_docs = await self.vector_rag.retrieve(query, max_results * 2)
        graph_docs = await self.graph_rag.retrieve(query, max_results * 2)

        # 第二階段：結果融合和去重
        all_docs = self._merge_and_deduplicate(vector_docs, graph_docs)

        # 第三階段：重排序（基於分數和多樣性）
        ranked_docs = self._rerank(all_docs, query, max_results)

        logger.info(f"高級檢索返回 {len(ranked_docs)} 個結果")
        return ranked_docs

    def _merge_and_deduplicate(self, docs1: List[Dict], docs2: List[Dict]) -> List[Dict]:
        """合並和去重"""
        # 簡單的基於內容的去重
        seen_content = set()
        merged = []

        for doc in docs1 + docs2:
            content_hash = hash(doc['content'][:100])  # 使用前100字符作為特徵
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                merged.append(doc)

        return merged

    def _rerank(self, docs: List[Dict], query: str, max_results: int) -> List[Dict]:
        """重排序文檔"""
        # 基於分數排序
        sorted_docs = sorted(docs, key=lambda x: x.get('score', 0), reverse=True)
        return sorted_docs[:max_results]


class AgenticRAG(RAGStrategy):
    """智能代理 RAG - 使用代理進行多步推理"""

    def __init__(self):
        super().__init__("Agentic RAG", "使用智能代理進行多步驟推理和檢索")
        self.hybrid_rag = HybridBalancedRAG()

    async def retrieve(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """代理式檢索"""
        # 第一步：分析查詢意圖
        intent = self._analyze_intent(query)

        # 第二步：根據意圖選擇檢索策略
        if intent == "relationship":
            # 關係類查詢，優先使用圖譜
            return await GraphOnlyRAG().retrieve(query, max_results)
        elif intent == "semantic":
            # 語義類查詢，優先使用向量
            return await VectorOnlyRAG().retrieve(query, max_results)
        else:
            # 混合查詢
            return await self.hybrid_rag.retrieve(query, max_results)

    def _analyze_intent(self, query: str) -> str:
        """分析查詢意圖（簡化版）"""
        # 關係關鍵詞
        relationship_keywords = ['關係', '影響', '比較', '差異', '聯繫', '之間']
        # 語義關鍵詞
        semantic_keywords = ['是什麼', '特點', '描述', '介紹', '說明']

        query_lower = query.lower()

        if any(kw in query_lower for kw in relationship_keywords):
            return "relationship"
        elif any(kw in query_lower for kw in semantic_keywords):
            return "semantic"
        else:
            return "hybrid"


class SelfRAG(RAGStrategy):
    """自我反思 RAG - 包含自我評估和迭代改進"""

    def __init__(self):
        super().__init__("Self RAG", "自我反思和迭代改進的 RAG")
        self.advanced_rag = AdvancedRAG()

    async def retrieve(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """自我反思式檢索"""
        # 第一次檢索
        docs = await self.advanced_rag.retrieve(query, max_results)

        # 自我評估：檢查結果質量
        quality_score = self._assess_quality(docs, query)

        # 如果質量不足，進行第二次檢索（使用改寫的查詢）
        if quality_score < 0.6:
            logger.info(f"首次檢索質量不足 ({quality_score:.2f})，進行查詢改寫")
            refined_query = self._refine_query(query)
            docs = await self.advanced_rag.retrieve(refined_query, max_results)

        return docs

    def _assess_quality(self, docs: List[Dict], query: str) -> float:
        """評估檢索結果質量（簡化版）"""
        if not docs:
            return 0.0

        # 基於文檔數量和平均分數
        avg_score = sum(doc.get('score', 0) for doc in docs) / len(docs)
        coverage = min(len(docs) / 5, 1.0)  # 期望至少5個結果

        return (avg_score + coverage) / 2

    def _refine_query(self, query: str) -> str:
        """改寫查詢（簡化版）"""
        # 實際應用中可以使用 LLM 進行查詢改寫
        return f"{query} 藝術史 相關資料"


# RAG 策略註冊表
RAG_STRATEGIES = {
    "vector_only": VectorOnlyRAG(),
    "graph_only": GraphOnlyRAG(),
    "hybrid_balanced": HybridBalancedRAG(),
    "advanced_rag": AdvancedRAG(),
    "agentic_rag": AgenticRAG(),
    "self_rag": SelfRAG()
}

# ==================== API 端點 ====================

@app.on_event("startup")
async def startup_event():
    """應用啟動時初始化連接"""
    global query_translator

    logger.info("🚀 RAG 管理器服務 V2 啟動中...")
    await conn_manager.initialize()

    # 初始化多語言翻譯器
    try:
        query_translator = MultilingualQueryTranslator()
        logger.info("✅ 多語言查詢翻譯器已初始化")
    except Exception as e:
        logger.warning(f"⚠️ 多語言翻譯器初始化失敗: {e}，將繼續使用原始查詢")
        query_translator = None

    logger.info("✅ RAG 管理器服務已就緒")

@app.on_event("shutdown")
async def shutdown_event():
    """應用關閉時清理連接"""
    logger.info("🛑 RAG 管理器服務關閉中...")
    await conn_manager.close()
    logger.info("✅ RAG 管理器服務已關閉")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康檢查端點"""
    services = conn_manager.get_health_status()

    # 檢查 Ollama
    try:
        response = await conn_manager.http_client.get(
            f"{OLLAMA_BASE_URL}/api/tags",
            timeout=5.0
        )
        services["ollama"] = response.status_code == 200
    except:
        services["ollama"] = False

    # 判斷整體狀態
    all_healthy = all(services.values())
    status = "healthy" if all_healthy else "degraded"

    return HealthResponse(
        status=status,
        services=services,
        timestamp=datetime.now().isoformat()
    )

@app.get("/api/v1/models")
async def list_models():
    """列出所有可用的模型組合"""
    return {
        "models": RAG_CONFIG.get("model_combinations", []),
        "total": len(RAG_CONFIG.get("model_combinations", []))
    }

@app.get("/api/v1/strategies")
async def list_strategies():
    """列出所有可用的 RAG 策略"""
    strategies = []
    for strategy_id, strategy_config in RAG_CONFIG.get("rag_strategies", {}).items():
        strategies.append({
            "id": strategy_id,
            "name": strategy_config.get("name"),
            "display_name": strategy_config.get("display_name"),
            "description": strategy_config.get("description"),
            "emoji": strategy_config.get("emoji")
        })
    return {
        "strategies": strategies,
        "total": len(strategies)
    }

@app.post("/api/v1/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """處理查詢請求"""
    start_time = datetime.now()

    # 解析模型組合 ID
    try:
        llm_model, rag_strategy = request.model_combination_id.split("@")
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"無效的模型組合 ID: {request.model_combination_id}，格式應為 'llm_model@rag_strategy'"
        )

    # 獲取 RAG 策略
    strategy = RAG_STRATEGIES.get(rag_strategy)
    if not strategy:
        raise HTTPException(
            status_code=404,
            detail=f"未找到 RAG 策略: {rag_strategy}"
        )

    # 多語言查詢翻譯
    original_query = request.query
    translation_info = None

    if query_translator:
        try:
            translation_result = query_translator.translate_query(request.query)
            translated_query = translation_result['translated_query']

            # 如果檢測到非英文且進行了翻譯，使用翻譯後的查詢
            if translation_result['detected_language'] != 'en' and translation_result['found_terms']:
                logger.info(
                    f"🌐 查詢翻譯: '{original_query}' -> '{translated_query}' "
                    f"({translation_result['detected_language']}, {len(translation_result['found_terms'])} 個術語)"
                )
                request.query = translated_query
                translation_info = {
                    'original_query': original_query,
                    'translated_query': translated_query,
                    'detected_language': translation_result['detected_language'],
                    'found_terms': translation_result['found_terms'],
                    'translation_method': translation_result['translation_method']
                }
        except Exception as e:
            logger.warning(f"⚠️ 查詢翻譯失敗: {e}，使用原始查詢")

    # 檢索階段
    retrieval_start = datetime.now()
    try:
        sources = await strategy.retrieve(request.query, request.max_results)
    except Exception as e:
        logger.error(f"檢索失敗: {e}")
        raise HTTPException(status_code=500, detail=f"檢索失敗: {str(e)}")
    retrieval_time = (datetime.now() - retrieval_start).total_seconds() * 1000

    # 生成階段
    generation_start = datetime.now()
    try:
        # 獲取模型參數
        temperature = request.temperature
        max_tokens = request.max_tokens

        # 如果沒有指定，從配置中獲取默認值
        if temperature is None or max_tokens is None:
            for combo in RAG_CONFIG.get("model_combinations", []):
                if combo["id"] == request.model_combination_id:
                    if temperature is None:
                        temperature = combo["params"].get("temperature", 0.1)
                    if max_tokens is None:
                        max_tokens = combo["params"].get("max_tokens", 2048)
                    break

        answer = await strategy.generate(
            request.query,
            sources,
            llm_model,
            temperature=temperature,
            max_tokens=max_tokens
        )
    except Exception as e:
        logger.error(f"生成失敗: {e}")
        raise HTTPException(status_code=500, detail=f"生成失敗: {str(e)}")
    generation_time = (datetime.now() - generation_start).total_seconds() * 1000

    total_time = (datetime.now() - start_time).total_seconds() * 1000

    # 構建響應
    metadata = {
        "total_time_ms": total_time,
        "num_sources": len(sources),
        "query_length": len(request.query),
        "answer_length": len(answer)
    }

    # 如果有翻譯信息，添加到元數據
    if translation_info:
        metadata["translation"] = translation_info

    response = QueryResponse(
        answer=answer,
        sources=sources if request.include_sources else [],
        model_used=llm_model,
        rag_strategy=rag_strategy,
        retrieval_time_ms=retrieval_time,
        generation_time_ms=generation_time,
        metadata=metadata
    )

    logger.info(
        f"查詢完成: {request.query[:50]}... | "
        f"模型: {llm_model} | 策略: {rag_strategy} | "
        f"總時間: {total_time:.0f}ms"
    )

    return response

@app.get("/")
async def root():
    """根端點"""
    return {
        "service": "Art History RAG Manager V2",
        "version": "2.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "models": "/api/v1/models",
            "strategies": "/api/v1/strategies",
            "query": "/api/v1/query"
        }
    }

# ==================== 主程序 ====================

if __name__ == "__main__":
    port = int(os.getenv("RAG_MANAGER_PORT", "8007"))

    logger.info(f"🚀 啟動 RAG 管理器服務於端口 {port}")
    logger.info(f"   Ollama: {OLLAMA_BASE_URL}")
    logger.info(f"   Neo4j: {NEO4J_URI}")
    logger.info(f"   ChromaDB: {CHROMADB_HOST}:{CHROMADB_PORT}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
