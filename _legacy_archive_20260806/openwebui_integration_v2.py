#!/usr/bin/env python3
"""
OpenWebUI 整合服務 V2
連接 OpenWebUI 到 RAG Manager V2
提供模型註冊和查詢轉發功能
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import httpx

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 創建 FastAPI 應用
app = FastAPI(
    title="OpenWebUI Integration Service V2",
    description="整合 OpenWebUI 與 RAG Manager V2",
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

# 配置（從環境變數讀取）
import os
RAG_MANAGER_URL = os.getenv("RAG_MANAGER_URL", "http://localhost:8007")
OPENWEBUI_URL = os.getenv("OPENWEBUI_URL", "http://localhost:8080")

# HTTP 客戶端
http_client = httpx.AsyncClient(timeout=120.0)

# ==================== 請求/響應模型 ====================

class ChatMessage(BaseModel):
    """聊天消息模型"""
    role: str
    content: str

class ChatRequest(BaseModel):
    """OpenWebUI 聊天請求"""
    model: str
    messages: List[ChatMessage]
    stream: bool = False
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None

class ChatResponse(BaseModel):
    """OpenWebUI 聊天響應"""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]

class ModelInfo(BaseModel):
    """模型信息"""
    id: str
    name: str
    description: str
    owned_by: str = "art-history-rag"
    permission: List[str] = []

# ==================== API 端點 ====================

@app.on_event("startup")
async def startup_event():
    """啟動時檢查 RAG 管理器連接"""
    logger.info("🚀 OpenWebUI 整合服務 V2 啟動中...")
    try:
        response = await http_client.get(f"{RAG_MANAGER_URL}/health")
        if response.status_code == 200:
            logger.info("✅ RAG 管理器連接成功")
        else:
            logger.warning(f"⚠️ RAG 管理器狀態異常: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ 無法連接到 RAG 管理器: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """關閉時清理資源"""
    logger.info("🛑 OpenWebUI 整合服務關閉中...")
    await http_client.aclose()
    logger.info("✅ OpenWebUI 整合服務已關閉")

@app.get("/")
async def root():
    """根端點"""
    return {
        "service": "OpenWebUI Integration Service V2",
        "version": "2.0.0",
        "status": "running",
        "rag_manager": RAG_MANAGER_URL,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """健康檢查"""
    # 檢查 RAG 管理器
    rag_manager_status = False
    try:
        response = await http_client.get(f"{RAG_MANAGER_URL}/health", timeout=5.0)
        rag_manager_status = response.status_code == 200
    except:
        pass

    return {
        "status": "healthy" if rag_manager_status else "degraded",
        "services": {
            "rag_manager": rag_manager_status
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/v1/models")
async def list_models():
    """列出所有可用的模型（OpenWebUI 兼容格式）"""
    try:
        # 從 RAG 管理器獲取模型列表
        response = await http_client.get(f"{RAG_MANAGER_URL}/api/v1/models")
        
        if response.status_code != 200:
            raise HTTPException(status_code=503, detail="RAG 管理器不可用")
        
        data = response.json()
        models = data.get("models", [])
        
        # 轉換為 OpenWebUI 格式
        openwebui_models = []
        for model in models:
            openwebui_models.append({
                "id": model["id"],
                "object": "model",
                "created": int(datetime.now().timestamp()),
                "owned_by": "art-history-rag",
                "permission": [],
                "root": model["id"],
                "parent": None,
                "name": model.get("display_name", model["name"]),
                "description": model.get("description", ""),
                "meta": model.get("meta", {})
            })
        
        logger.info(f"📋 返回 {len(openwebui_models)} 個模型")
        
        return {
            "object": "list",
            "data": openwebui_models
        }
        
    except httpx.RequestError as e:
        logger.error(f"❌ 連接 RAG 管理器失敗: {e}")
        raise HTTPException(status_code=503, detail=f"無法連接到 RAG 管理器: {str(e)}")
    except Exception as e:
        logger.error(f"❌ 列出模型失敗: {e}")
        raise HTTPException(status_code=500, detail=f"列出模型失敗: {str(e)}")

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    """OpenWebUI 聊天補全端點"""
    try:
        logger.info(f"💬 收到聊天請求: 模型={request.model}, 消息數={len(request.messages)}")
        
        # 提取最後一條用戶消息作為查詢
        user_messages = [msg for msg in request.messages if msg.role == "user"]
        if not user_messages:
            raise HTTPException(status_code=400, detail="沒有用戶消息")
        
        query = user_messages[-1].content
        
        # 構建 RAG 管理器請求
        rag_request = {
            "query": query,
            "model_combination_id": request.model,
            "max_results": 5,
            "include_sources": True
        }
        
        if request.temperature is not None:
            rag_request["temperature"] = request.temperature
        if request.max_tokens is not None:
            rag_request["max_tokens"] = request.max_tokens
        
        # 調用 RAG 管理器
        logger.info(f"🔄 轉發請求到 RAG 管理器: {query[:50]}...")
        response = await http_client.post(
            f"{RAG_MANAGER_URL}/api/v1/query",
            json=rag_request,
            timeout=120.0
        )
        
        if response.status_code != 200:
            error_detail = response.text
            logger.error(f"❌ RAG 管理器返回錯誤: {error_detail}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"RAG 管理器錯誤: {error_detail}"
            )
        
        rag_result = response.json()
        answer = rag_result.get("answer", "")
        sources = rag_result.get("sources", [])
        
        # 構建帶來源的完整回答
        full_answer = answer
        if sources:
            full_answer += "\n\n📚 **參考來源**:\n"
            for i, source in enumerate(sources[:3], 1):
                source_name = source.get("source", "未知來源")
                full_answer += f"{i}. {source_name}\n"
        
        # 添加元數據
        metadata = rag_result.get("metadata", {})
        full_answer += f"\n\n⚙️ **處理信息**:\n"
        full_answer += f"- 模型: {rag_result.get('model_used', 'N/A')}\n"
        full_answer += f"- RAG策略: {rag_result.get('rag_strategy', 'N/A')}\n"
        full_answer += f"- 檢索時間: {rag_result.get('retrieval_time_ms', 0):.0f}ms\n"
        full_answer += f"- 生成時間: {rag_result.get('generation_time_ms', 0):.0f}ms\n"
        
        # 構建 OpenWebUI 格式的響應
        completion_response = {
            "id": f"chatcmpl-{int(datetime.now().timestamp())}",
            "object": "chat.completion",
            "created": int(datetime.now().timestamp()),
            "model": request.model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": full_answer
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": len(query),
                "completion_tokens": len(answer),
                "total_tokens": len(query) + len(answer)
            }
        }
        
        logger.info(f"✅ 查詢成功: {len(answer)} 字符")
        return completion_response
        
    except httpx.RequestError as e:
        logger.error(f"❌ 連接 RAG 管理器失敗: {e}")
        raise HTTPException(status_code=503, detail=f"無法連接到 RAG 管理器: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 聊天補全失敗: {e}")
        raise HTTPException(status_code=500, detail=f"聊天補全失敗: {str(e)}")

@app.get("/v1/models/{model_id}")
async def get_model(model_id: str):
    """獲取特定模型信息"""
    try:
        # 從 RAG 管理器獲取所有模型
        response = await http_client.get(f"{RAG_MANAGER_URL}/api/v1/models")
        
        if response.status_code != 200:
            raise HTTPException(status_code=503, detail="RAG 管理器不可用")
        
        data = response.json()
        models = data.get("models", [])
        
        # 查找指定模型
        model = next((m for m in models if m["id"] == model_id), None)
        
        if not model:
            raise HTTPException(status_code=404, detail=f"模型未找到: {model_id}")
        
        return {
            "id": model["id"],
            "object": "model",
            "created": int(datetime.now().timestamp()),
            "owned_by": "art-history-rag",
            "name": model.get("display_name", model["name"]),
            "description": model.get("description", ""),
            "meta": model.get("meta", {})
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 獲取模型信息失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取模型信息失敗: {str(e)}")

@app.get("/api/models")
async def list_models_simple():
    """簡單模型列表（備用端點）"""
    try:
        response = await http_client.get(f"{RAG_MANAGER_URL}/api/v1/models")
        
        if response.status_code != 200:
            raise HTTPException(status_code=503, detail="RAG 管理器不可用")
        
        data = response.json()
        models = data.get("models", [])
        
        # 簡化的模型列表
        simple_models = [
            {
                "id": m["id"],
                "name": m.get("display_name", m["name"]),
                "description": m.get("description", "")
            }
            for m in models
        ]
        
        return {
            "models": simple_models,
            "total": len(simple_models)
        }
        
    except Exception as e:
        logger.error(f"❌ 列出模型失敗: {e}")
        raise HTTPException(status_code=500, detail=f"列出模型失敗: {str(e)}")

@app.get("/api/rag/strategies")
async def list_rag_strategies():
    """列出所有 RAG 策略"""
    try:
        response = await http_client.get(f"{RAG_MANAGER_URL}/api/v1/strategies")
        
        if response.status_code != 200:
            raise HTTPException(status_code=503, detail="RAG 管理器不可用")
        
        return response.json()
        
    except Exception as e:
        logger.error(f"❌ 列出 RAG 策略失敗: {e}")
        raise HTTPException(status_code=500, detail=f"列出 RAG 策略失敗: {str(e)}")

# ==================== 主程序 ====================

if __name__ == "__main__":
    import os
    
    port = int(os.getenv("INTEGRATION_PORT", "8009"))
    
    logger.info(f"🚀 啟動 OpenWebUI 整合服務於端口 {port}")
    logger.info(f"   RAG Manager: {RAG_MANAGER_URL}")
    logger.info(f"   OpenWebUI: {OPENWEBUI_URL}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
