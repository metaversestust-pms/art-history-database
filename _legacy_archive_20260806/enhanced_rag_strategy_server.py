#!/usr/bin/env python3
"""
增強型 RAG 策略服務器
集成增強型 Neo4j 檢索器，提供更精確的檢索功能
"""

import asyncio
import logging
import json
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime
import sys
import os

# 添加 langchain-rag 目錄到路徑
sys.path.append('./langchain-rag')

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== 請求/響應模型 ====================

class QueryRequest(BaseModel):
    query: str = Field(..., description="用戶查詢")
    strategy: str = Field("hybrid_balanced", description="RAG策略")
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
    title="增強型藝術史RAG策略API",
    description="提供增強型Neo4j檢索的RAG接口",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 全局變量 ====================

enhanced_retriever = None
ollama_url = "http://localhost:11434"
retriever_config = None

# ==================== 初始化 ====================

@app.on_event("startup")
async def startup_event():
    """啟動時初始化增強型檢索器"""
    global enhanced_retriever, retriever_config

    try:
        from sentence_transformers import SentenceTransformer

        # 直接從當前目錄的 langchain-rag 導入
        import sys
        import os
        retriever_path = os.path.join(os.path.dirname(__file__), 'langchain-rag')
        if retriever_path not in sys.path:
            sys.path.insert(0, retriever_path)

        from enhanced_neo4j_retriever import (
            create_enhanced_retriever,
            RetrieverConfig
        )

        logger.info("🚀 初始化增強型RAG系統...")

        # 初始化嵌入模型
        class LocalEmbeddings:
            def __init__(self):
                self.model = SentenceTransformer('BAAI/bge-small-zh-v1.5')

            def embed_query(self, text: str):
                return self.model.encode(text).tolist()

        embeddings = LocalEmbeddings()

        # 配置檢索器
        retriever_config = RetrieverConfig(
            neo4j_uri="bolt://localhost:7687",
            neo4j_user="neo4j",
            neo4j_password="arthistory123",
            top_k_initial=20,
            top_k_final=5,
            enable_reranking=True,
            vector_weight=0.4,
            fulltext_weight=0.3,
            graph_weight=0.3
        )

        # 創建檢索器（不使用LLM，節省資源）
        enhanced_retriever = create_enhanced_retriever(
            embedding_model=embeddings,
            llm=None,  # 暫時不使用LLM進行查詢擴展
            config=retriever_config
        )

        logger.info("✅ 增強型檢索器初始化成功")

    except ImportError as e:
        logger.warning(f"⚠️ 無法載入增強型檢索器: {e}")
        logger.info("   將使用基礎模式")
    except Exception as e:
        logger.error(f"❌ 初始化失敗: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """關閉時清理資源"""
    global enhanced_retriever

    if enhanced_retriever:
        try:
            enhanced_retriever.close()
            logger.info("✅ 資源清理完成")
        except:
            pass

# ==================== API 端點 ====================

@app.get("/")
async def root():
    return {
        "service": "增強型藝術史RAG策略API",
        "version": "2.0.0",
        "status": "running",
        "enhanced_retrieval": enhanced_retriever is not None,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """健康檢查"""
    return {
        "status": "healthy",
        "enhanced_retriever": "available" if enhanced_retriever else "unavailable",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/strategies")
async def list_strategies():
    """列出支持的RAG策略"""
    strategies = [
        {
            "name": "vector_only",
            "display": "向量RAG",
            "description": "純向量相似度檢索（語義搜索）"
        },
        {
            "name": "graph_only",
            "display": "圖譜RAG",
            "description": "知識圖譜推理（結構化查詢）"
        },
        {
            "name": "hybrid_balanced",
            "display": "混合RAG",
            "description": "平衡向量、全文和圖譜檢索"
        },
        {
            "name": "enhanced_rag",
            "display": "增強RAG",
            "description": "多策略融合 + Re-ranker重排序"
        }
    ]

    return {
        "strategies": strategies,
        "enhanced_features": {
            "vector_search": True,
            "fulltext_search": True,
            "graph_search": True,
            "query_expansion": False,  # LLM查詢擴展需要額外配置
            "reranking": enhanced_retriever is not None and retriever_config.enable_reranking
        }
    }

@app.get("/system/status")
async def system_status():
    """系統狀態"""
    from neo4j import GraphDatabase

    status = {
        "timestamp": datetime.now().isoformat(),
        "components": {
            "enhanced_retriever": enhanced_retriever is not None,
            "reranker": retriever_config.enable_reranking if retriever_config else False,
        },
        "neo4j": {}
    }

    # 檢查 Neo4j 連接
    try:
        driver = GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "arthistory123")
        )
        with driver.session() as session:
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

        driver.close()
    except Exception as e:
        status["neo4j"] = {
            "connected": False,
            "error": str(e)
        }

    return status

def query_enhanced_rag(query: str, strategy: str, top_k: int = 5) -> Dict[str, Any]:
    """使用增強型檢索器查詢"""
    if not enhanced_retriever:
        return {
            "sources": [],
            "context": "",
            "metadata": {"error": "增強型檢索器未初始化"}
        }

    try:
        import time
        start_time = time.time()

        # 使用增強型檢索器
        docs = enhanced_retriever.get_relevant_documents(query)

        retrieval_time = time.time() - start_time

        # 轉換為標準格式
        sources = []
        for doc in docs[:top_k]:
            sources.append({
                "content": doc.page_content,
                "source": "neo4j",
                "score": doc.metadata.get('score', 0),
                "retrieval_method": doc.metadata.get('retrieval_method', 'unknown'),
                "labels": doc.metadata.get('labels', []),
                "metadata": doc.metadata
            })

        # 構建上下文
        context = "\n\n".join(doc.page_content for doc in docs[:top_k])

        return {
            "sources": sources,
            "context": context,
            "metadata": {
                "strategy": strategy,
                "retrieval_time": retrieval_time,
                "num_results": len(sources),
                "enhanced_features": {
                    "vector_search": True,
                    "fulltext_search": True,
                    "reranking": retriever_config.enable_reranking if retriever_config else False
                }
            }
        }

    except Exception as e:
        logger.error(f"❌ 增強型檢索失敗: {e}")
        return {
            "sources": [],
            "context": "",
            "metadata": {"error": str(e)}
        }

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

    # 1. 使用增強型檢索器查詢
    if request.use_enhanced_retrieval and enhanced_retriever:
        rag_result = query_enhanced_rag(request.query, request.strategy, request.top_k)
    else:
        # 降級到基礎模式
        rag_result = {
            "sources": [],
            "context": "基礎檢索模式（增強型檢索器未啟用）",
            "metadata": {"mode": "basic"}
        }

    # 2. 構建增強提示詞
    if rag_result["sources"]:
        context_text = "\n\n相關藝術史資料：\n"
        for i, source in enumerate(rag_result["sources"][:3], 1):
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
    metadata = rag_result.get("metadata", {})
    metadata["llm_model"] = request.base_model
    metadata["query_strategy"] = request.strategy

    # 添加來源信息到答案
    if rag_result["sources"]:
        answer += "\n\n---\n📚 **檢索信息**:\n"
        answer += f"- 策略: {request.strategy}\n"
        answer += f"- 找到 {len(rag_result['sources'])} 個相關資料\n"
        answer += f"- 檢索時間: {metadata.get('retrieval_time', 0):.3f}秒\n"

        if metadata.get('enhanced_features'):
            features = metadata['enhanced_features']
            answer += "- 使用功能: "
            enabled = []
            if features.get('vector_search'): enabled.append("向量搜索")
            if features.get('fulltext_search'): enabled.append("全文搜索")
            if features.get('reranking'): enabled.append("重排序")
            answer += ", ".join(enabled) + "\n"

    return QueryResponse(
        answer=answer,
        strategy_used=request.strategy,
        sources=rag_result["sources"],
        model_used=request.base_model,
        metadata=metadata
    )

@app.post("/batch_query")
async def batch_query(queries: List[str], strategy: str = "hybrid_balanced"):
    """批量查詢"""
    results = []
    for query in queries[:5]:  # 限制批量查詢數量
        request = QueryRequest(query=query, strategy=strategy)
        result = await process_query(request)
        results.append(result)

    return {"results": results, "total": len(results)}

# ==================== 主程序 ====================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🎨 啟動增強型藝術史RAG策略API")
    print("="*60)
    print("📚 API文檔: http://localhost:8009/docs")
    print("🔄 健康檢查: http://localhost:8009/health")
    print("📊 系統狀態: http://localhost:8009/system/status")
    print("📋 策略列表: http://localhost:8009/strategies")
    print("="*60 + "\n")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8009,  # 改用 8009 避免與現有服務衝突
        log_level="info"
    )
