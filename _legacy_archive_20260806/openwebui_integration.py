#!/usr/bin/env python3
"""
OpenWebUI與統一RAG管理API集成腳本
作為OpenWebUI的自定義RAG提供者
"""

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import uvicorn

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 統一RAG管理API配置
RAG_API_URL = "http://localhost:8002"

class OpenWebUIRAGRequest(BaseModel):
    """OpenWebUI RAG請求格式"""
    query: str
    collection_name: Optional[str] = None
    top_k: int = 5
    filters: Optional[Dict] = None

class OpenWebUIRAGResponse(BaseModel):
    """OpenWebUI RAG響應格式"""
    sources: List[Dict[str, Any]]
    context: str
    metadata: Dict[str, Any]

# 創建FastAPI應用
app = FastAPI(
    title="OpenWebUI RAG集成服務",
    description="連接OpenWebUI到藝術史統一RAG管理系統",
    version="1.0.0"
)

# 添加CORS支持
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """根端點"""
    return {
        "service": "OpenWebUI RAG集成服務",
        "status": "running",
        "rag_api_url": RAG_API_URL
    }

@app.get("/health")
async def health_check():
    """健康檢查"""
    try:
        # 檢查統一RAG管理API的健康狀態
        response = requests.get(f"{RAG_API_URL}/health", timeout=5)
        if response.status_code == 200:
            return {
                "status": "healthy",
                "rag_api_status": "connected",
                "message": "成功連接到統一RAG管理API"
            }
        else:
            return {
                "status": "degraded",
                "rag_api_status": "error",
                "message": f"RAG API返回狀態: {response.status_code}"
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "rag_api_status": "disconnected",
            "message": f"無法連接到RAG API: {e}"
        }

@app.post("/rag/query", response_model=OpenWebUIRAGResponse)
async def rag_query(request: OpenWebUIRAGRequest):
    """處理OpenWebUI的RAG查詢請求"""
    try:
        logger.info(f"收到OpenWebUI RAG查詢: {request.query}")

        # 準備發送到統一RAG管理API的請求
        rag_request = {
            "query": request.query,
            "strategy": "hybrid_balanced",  # 使用混合策略
            "top_k": request.top_k,
            "include_sources": True
        }

        # 調用統一RAG管理API
        response = requests.post(
            f"{RAG_API_URL}/query",
            json=rag_request,
            timeout=30
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"RAG API錯誤: {response.text}"
            )

        rag_result = response.json()

        if not rag_result.get('success', False):
            raise HTTPException(
                status_code=500,
                detail=f"RAG查詢失敗: {rag_result.get('answer', '未知錯誤')}"
            )

        # 轉換為OpenWebUI格式的響應
        sources = []
        if rag_result.get('sources'):
            for source in rag_result['sources']:
                sources.append({
                    "id": source.get('id', ''),
                    "content": source.get('content', ''),
                    "metadata": source.get('metadata', {}),
                    "score": source.get('score', 0.0),
                    "source": source.get('source', 'Neo4j GraphRAG')
                })

        # 構建上下文文本
        context = f"""
基於藝術史知識圖譜的回答：

{rag_result.get('answer', '')}

處理策略: {rag_result.get('strategy_used', 'hybrid_balanced')}
信心分數: {rag_result.get('confidence_score', 0.0):.2f}
處理時間: {rag_result.get('processing_time', 0.0):.3f}秒
"""

        response_data = OpenWebUIRAGResponse(
            sources=sources,
            context=context.strip(),
            metadata={
                "strategy_used": rag_result.get('strategy_used', 'hybrid_balanced'),
                "confidence_score": rag_result.get('confidence_score', 0.0),
                "processing_time": rag_result.get('processing_time', 0.0),
                "cache_hit": rag_result.get('cache_hit', False),
                "source_system": "Neo4j GraphRAG"
            }
        )

        logger.info(f"✅ 成功處理OpenWebUI RAG查詢: {len(sources)}個數據源")
        return response_data

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ RAG API請求失敗: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"無法連接到RAG服務: {str(e)}"
        )
    except Exception as e:
        logger.error(f"❌ RAG查詢處理失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"RAG查詢處理失敗: {str(e)}"
        )

@app.get("/rag/collections")
async def get_collections():
    """獲取可用的RAG集合（兼容OpenWebUI）"""
    return {
        "collections": [
            {
                "name": "art_history_knowledge_graph",
                "description": "藝術史知識圖譜數據集",
                "document_count": "未知",
                "metadata": {
                    "source": "Neo4j GraphRAG",
                    "type": "knowledge_graph",
                    "domain": "art_history"
                }
            }
        ]
    }

@app.get("/rag/config")
async def get_rag_config():
    """獲取RAG配置（兼容OpenWebUI）"""
    try:
        # 從統一RAG管理API獲取系統狀態
        response = requests.get(f"{RAG_API_URL}/system/status", timeout=10)
        if response.status_code == 200:
            status = response.json()
            return {
                "provider": "Neo4j GraphRAG",
                "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
                "chunk_size": 500,
                "chunk_overlap": 50,
                "top_k": 5,
                "configuration": status.get('configuration', {}),
                "components": status.get('components', {}),
                "strategies": ["vector_only", "graph_only", "hybrid_balanced", "adaptive", "specialized"]
            }
        else:
            return {
                "provider": "Neo4j GraphRAG",
                "status": "配置獲取失敗"
            }
    except Exception as e:
        return {
            "provider": "Neo4j GraphRAG",
            "status": f"配置獲取錯誤: {e}"
        }

if __name__ == "__main__":
    print("🚀 啟動OpenWebUI RAG集成服務...")
    print(f"🔗 連接到統一RAG管理API: {RAG_API_URL}")
    print("📚 API文檔: http://localhost:8009/docs")

    uvicorn.run(
        "openwebui_integration:app",
        host="0.0.0.0",
        port=8009,
        reload=True,
        log_level="info"
    )