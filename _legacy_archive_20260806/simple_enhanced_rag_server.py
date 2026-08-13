#!/usr/bin/env python3
"""
簡化版增強型 RAG 策略服務器
不依賴 LangChain，直接使用 Neo4j 和 SentenceTransformer
"""

import logging
import requests
from typing import Dict, List, Any
from datetime import datetime
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== 請求/響應模型 ====================

class QueryRequest(BaseModel):
    query: str = Field(..., description="用戶查詢")
    strategy: str = Field("enhanced_rag", description="RAG策略")
    base_model: str = Field("llama3.1:8b", description="基礎LLM模型")
    top_k: int = Field(5, description="檢索結果數量")
    use_enhanced_retrieval: bool = Field(True, description="使用增強型檢索")

class QueryResponse(BaseModel):
    answer: str
    strategy_used: str
    sources: List[Dict[str, Any]] = []
    model_used: str
    metadata: Dict[str, Any] = {}

# ==================== FastAPI App ====================

app = FastAPI(
    title="簡化版增強型藝術史RAG API",
    description="直接使用Neo4j向量+全文檢索",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 全局變量 ====================

embedding_model = None
neo4j_driver = None
ollama_url = "http://localhost:11434"

# ==================== 初始化 ====================

@app.on_event("startup")
async def startup_event():
    """啟動時初始化"""
    global embedding_model, neo4j_driver

    try:
        logger.info("🚀 初始化簡化版增強型RAG系統...")

        # 初始化嵌入模型
        logger.info("📥 載入嵌入模型...")
        embedding_model = SentenceTransformer('BAAI/bge-small-zh-v1.5')
        logger.info(f"✅ 嵌入模型載入完成（{embedding_model.get_sentence_embedding_dimension()}維）")

        # 連接 Neo4j
        logger.info("🔗 連接 Neo4j...")
        neo4j_driver = GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "arthistory123")
        )
        # 測試連接
        with neo4j_driver.session() as session:
            session.run("RETURN 1")
        logger.info("✅ Neo4j 連接成功")

        logger.info("✅ 簡化版增強型RAG系統初始化完成")

    except Exception as e:
        logger.error(f"❌ 初始化失敗: {e}")
        import traceback
        traceback.print_exc()

@app.on_event("shutdown")
async def shutdown_event():
    """關閉時清理資源"""
    global neo4j_driver

    if neo4j_driver:
        try:
            neo4j_driver.close()
            logger.info("✅ 資源清理完成")
        except:
            pass

# ==================== API 端點 ====================

@app.get("/")
async def root():
    return {
        "service": "簡化版增強型藝術史RAG API",
        "version": "1.0.0",
        "status": "running",
        "enhanced_retrieval": embedding_model is not None and neo4j_driver is not None,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """健康檢查"""
    return {
        "status": "healthy",
        "embedding_model": "available" if embedding_model else "unavailable",
        "neo4j": "available" if neo4j_driver else "unavailable",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/system/status")
async def system_status():
    """系統狀態"""
    status = {
        "timestamp": datetime.now().isoformat(),
        "components": {
            "embedding_model": embedding_model is not None,
            "neo4j_driver": neo4j_driver is not None,
        },
        "neo4j": {}
    }

    # 檢查 Neo4j 狀態
    if neo4j_driver:
        try:
            with neo4j_driver.session() as session:
                result = session.run("MATCH (n) RETURN count(n) as count")
                node_count = result.single()['count']

                result = session.run("""
                    MATCH (a:Artist)
                    WHERE a.name_embedding IS NOT NULL
                    RETURN count(a) as count
                """)
                artist_embeddings = result.single()['count']

                result = session.run("""
                    MATCH (w:Artwork)
                    WHERE w.title_embedding IS NOT NULL
                    RETURN count(w) as count
                """)
                artwork_embeddings = result.single()['count']

                status["neo4j"] = {
                    "connected": True,
                    "total_nodes": node_count,
                    "artist_embeddings": artist_embeddings,
                    "artwork_embeddings": artwork_embeddings
                }
        except Exception as e:
            status["neo4j"] = {
                "connected": False,
                "error": str(e)
            }

    return status

def hybrid_retrieval(query: str, top_k: int = 5) -> List[Dict]:
    """混合檢索：向量 + 全文"""
    if not embedding_model or not neo4j_driver:
        return []

    results = []

    try:
        # 生成查詢向量
        query_embedding = embedding_model.encode(query).tolist()

        with neo4j_driver.session() as session:
            # 1. 向量搜索藝術家
            try:
                vector_results = session.run("""
                    CALL db.index.vector.queryNodes('artist_name_embeddings', $top_k, $embedding)
                    YIELD node, score
                    RETURN node.name as name,
                           node.biography as biography,
                           'Artist' as type,
                           'vector' as method,
                           score
                    ORDER BY score DESC
                """, {'embedding': query_embedding, 'top_k': top_k})

                for record in vector_results:
                    results.append({
                        "content": f"{record['name']}: {record.get('biography', '')[:200]}",
                        "score": record['score'],
                        "retrieval_method": "vector",
                        "type": record['type'],
                        "source": "neo4j"
                    })
            except Exception as e:
                logger.warning(f"向量搜索藝術家失敗: {e}")

            # 2. 向量搜索作品
            try:
                vector_results = session.run("""
                    CALL db.index.vector.queryNodes('artwork_title_embeddings', $top_k, $embedding)
                    YIELD node, score
                    RETURN node.title as title,
                           node.description as description,
                           'Artwork' as type,
                           'vector' as method,
                           score
                    ORDER BY score DESC
                """, {'embedding': query_embedding, 'top_k': top_k})

                for record in vector_results:
                    results.append({
                        "content": f"{record['title']}: {record.get('description', '')[:200]}",
                        "score": record['score'],
                        "retrieval_method": "vector",
                        "type": record['type'],
                        "source": "neo4j"
                    })
            except Exception as e:
                logger.warning(f"向量搜索作品失敗: {e}")

            # 3. 全文搜索藝術家
            try:
                fulltext_results = session.run("""
                    CALL db.index.fulltext.queryNodes('artist_fulltext', $query)
                    YIELD node, score
                    RETURN node.name as name,
                           node.biography as biography,
                           'Artist' as type,
                           'fulltext' as method,
                           score
                    ORDER BY score DESC
                    LIMIT $top_k
                """, {'query': query, 'top_k': top_k})

                for record in fulltext_results:
                    results.append({
                        "content": f"{record['name']}: {record.get('biography', '')[:200]}",
                        "score": record['score'],
                        "retrieval_method": "fulltext",
                        "type": record['type'],
                        "source": "neo4j"
                    })
            except Exception as e:
                logger.warning(f"全文搜索藝術家失敗: {e}")

            # 4. 全文搜索作品
            try:
                fulltext_results = session.run("""
                    CALL db.index.fulltext.queryNodes('artwork_fulltext', $query)
                    YIELD node, score
                    RETURN node.title as title,
                           node.description as description,
                           'Artwork' as type,
                           'fulltext' as method,
                           score
                    ORDER BY score DESC
                    LIMIT $top_k
                """, {'query': query, 'top_k': top_k})

                for record in fulltext_results:
                    results.append({
                        "content": f"{record['title']}: {record.get('description', '')[:200]}",
                        "score": record['score'],
                        "retrieval_method": "fulltext",
                        "type": record['type'],
                        "source": "neo4j"
                    })
            except Exception as e:
                logger.warning(f"全文搜索作品失敗: {e}")

    except Exception as e:
        logger.error(f"混合檢索失敗: {e}")

    # 去重並排序
    seen = set()
    unique_results = []
    for r in sorted(results, key=lambda x: x['score'], reverse=True):
        content_key = r['content'][:50]
        if content_key not in seen:
            seen.add(content_key)
            unique_results.append(r)

    return unique_results[:top_k]

def query_ollama(model: str, prompt: str) -> str:
    """查詢Ollama模型"""
    try:
        response = requests.post(
            f"{ollama_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 2048
                }
            },
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            return result.get("response", "")
    except Exception as e:
        logger.error(f"Ollama查詢失敗: {e}")

    return "抱歉，模型查詢失敗。"

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """處理RAG+LLM查詢"""

    logger.info(f"🔍 收到查詢: {request.query} (策略: {request.strategy})")

    start_time = time.time()

    # 1. 混合檢索
    sources = hybrid_retrieval(request.query, request.top_k)

    retrieval_time = time.time() - start_time

    # 2. 構建增強提示詞
    if sources:
        context_text = "\n\n相關藝術史資料：\n"
        for i, source in enumerate(sources[:3], 1):
            content = source.get("content", "")[:300]
            method = source.get("retrieval_method", "unknown")
            score = source.get("score", 0)
            context_text += f"\n[{i}] (檢索方法: {method}, 分數: {score:.3f})\n{content}\n"

        enhanced_prompt = f"""基於以下藝術史知識庫資料回答問題：

{context_text}

問題：{request.query}

請基於上述資料提供專業的藝術史解答。如果資料不足，請說明並提供一般性建議。
"""
    else:
        enhanced_prompt = f"""作為藝術史專家，請回答以下問題：

問題：{request.query}

請提供專業的藝術史解答。
（注意：未找到相關資料庫資料）
"""

    # 3. 查詢LLM
    answer = query_ollama(request.base_model, enhanced_prompt)

    # 4. 添加元數據
    metadata = {
        "strategy": request.strategy,
        "retrieval_time": retrieval_time,
        "num_results": len(sources),
        "llm_model": request.base_model,
        "enhanced_features": {
            "vector_search": True,
            "fulltext_search": True,
            "graph_search": False,
            "reranking": False
        }
    }

    # 添加檢索信息到答案
    if sources:
        answer += "\n\n---\n📚 **檢索信息**:\n"
        answer += f"- 策略: {request.strategy}\n"
        answer += f"- 找到 {len(sources)} 個相關資料\n"
        answer += f"- 檢索時間: {retrieval_time:.3f}秒\n"
        answer += "- 使用功能: 向量搜索, 全文搜索\n"

    return QueryResponse(
        answer=answer,
        strategy_used=request.strategy,
        sources=sources,
        model_used=request.base_model,
        metadata=metadata
    )

# ==================== 主程序 ====================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🎨 啟動簡化版增強型藝術史RAG API")
    print("="*60)
    print("📚 API文檔: http://localhost:8009/docs")
    print("🔄 健康檢查: http://localhost:8009/health")
    print("📊 系統狀態: http://localhost:8009/system/status")
    print("="*60 + "\n")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8009,
        log_level="info"
    )
