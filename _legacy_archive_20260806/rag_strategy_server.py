#!/usr/bin/env python3
"""
RAG策略服務器 - 為不同的RAG+LLM組合提供API端點
"""

import asyncio
import logging
import json
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime
import sys
import os

# 添加langchain-rag目錄到路徑
sys.path.append('./langchain-rag')

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# 嘗試導入RAG組件
try:
    from integrated_rag_optimizer import IntegratedRAGOptimizer, RAGStrategy
    rag_available = True
except ImportError:
    rag_available = False
    print("警告: 無法導入RAG組件，將使用模擬模式")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="藝術史RAG策略API",
    description="為OpenWebUI提供不同RAG策略的接口",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str = Field(..., description="用戶查詢")
    strategy: str = Field("hybrid_balanced", description="RAG策略")
    base_model: str = Field("llama3.1:8b", description="基礎LLM模型")
    top_k: int = Field(5, description="檢索結果數量")

class QueryResponse(BaseModel):
    answer: str
    strategy_used: str
    sources: List[Dict[str, Any]] = []
    model_used: str

# 全局RAG優化器
rag_optimizer = None
ollama_url = "http://localhost:11434"

@app.on_event("startup")
async def startup_event():
    """啟動時初始化RAG系統"""
    global rag_optimizer

    if rag_available:
        try:
            logger.info("🚀 初始化RAG系統...")
            rag_optimizer = IntegratedRAGOptimizer()
            if rag_optimizer.initialize_components():
                logger.info("✅ RAG系統初始化成功")
            else:
                logger.error("❌ RAG系統初始化失敗")
        except Exception as e:
            logger.error(f"❌ RAG初始化異常: {e}")

@app.get("/")
async def root():
    return {
        "service": "藝術史RAG策略API",
        "version": "1.0.0",
        "status": "running",
        "rag_available": rag_available,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """健康檢查"""
    return {
        "status": "healthy",
        "rag_system": "available" if rag_optimizer else "unavailable",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/strategies")
async def list_strategies():
    """列出支持的RAG策略"""
    if rag_available:
        strategies = [
            {
                "name": "vector_only",
                "display": "向量RAG",
                "description": "純向量相似度檢索"
            },
            {
                "name": "graph_only",
                "display": "圖譜RAG",
                "description": "知識圖譜推理"
            },
            {
                "name": "hybrid_balanced",
                "display": "混合RAG",
                "description": "平衡向量與圖譜"
            },
            {
                "name": "adaptive",
                "display": "自適應RAG",
                "description": "動態選擇最佳策略"
            },
            {
                "name": "specialized",
                "display": "專門RAG",
                "description": "基於查詢類型選擇"
            }
        ]
    else:
        strategies = [
            {
                "name": "mock_vector",
                "display": "模擬向量RAG",
                "description": "模擬向量檢索（測試用）"
            }
        ]

    return {"strategies": strategies}

def query_rag_system(query: str, strategy: str, top_k: int = 5) -> Dict[str, Any]:
    """查詢RAG系統"""
    if not rag_available or not rag_optimizer:
        return {
            "sources": [],
            "context": f"模擬RAG回應（策略: {strategy}）",
            "metadata": {"strategy": strategy, "mode": "mock"}
        }

    try:
        # 使用統一RAG管理器查詢
        result = rag_optimizer.process_query(
            query=query,
            strategy_name=strategy,
            top_k=top_k
        )

        if result and result.success:
            return {
                "sources": [asdict(source) for source in result.sources],
                "context": result.enhanced_context,
                "metadata": {
                    "strategy": result.strategy_used,
                    "confidence": result.confidence_score,
                    "processing_time": result.processing_time
                }
            }
    except Exception as e:
        logger.error(f"RAG查詢失敗: {e}")

    return {
        "sources": [],
        "context": "",
        "metadata": {"strategy": strategy, "error": "查詢失敗"}
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

    # 1. 使用指定策略查詢RAG系統
    rag_result = query_rag_system(request.query, request.strategy, request.top_k)

    # 2. 構建增強提示詞
    if rag_result["sources"]:
        context_text = "\n\n相關藝術史資料：\n"
        for i, source in enumerate(rag_result["sources"][:3], 1):
            title = source.get("title", "Unknown")
            content = source.get("content", "")[:200] + "..."
            context_text += f"{i}. {title}: {content}\n"

        enhanced_prompt = f"""基於以下藝術史知識庫資料回答問題：

{context_text}

問題：{request.query}

請基於上述資料提供專業的藝術史解答，如果資料不足，請說明並提供一般性建議。

當前使用的RAG策略: {request.strategy}"""
    else:
        enhanced_prompt = f"""作為藝術史專家，請回答以下問題：

問題：{request.query}

請提供專業的藝術史解答。

當前使用的RAG策略: {request.strategy}（未找到相關資料）"""

    # 3. 查詢LLM
    answer = query_ollama(request.base_model, enhanced_prompt)

    # 4. 添加策略標識
    answer += f"\n\n---\n🔧 RAG策略: {request.strategy}\n📊 基礎模型: {request.base_model}"

    return QueryResponse(
        answer=answer,
        strategy_used=request.strategy,
        sources=rag_result["sources"],
        model_used=request.base_model
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

if __name__ == "__main__":
    print("🎨 啟動藝術史RAG策略API...")
    print("📚 API文檔: http://localhost:8006/docs")
    print("🔄 健康檢查: http://localhost:8006/health")
    print("📋 策略列表: http://localhost:8006/strategies")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8006,
        log_level="info"
    )