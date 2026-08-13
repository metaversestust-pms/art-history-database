"""
title: 藝術史 RAG+LLM 智能組合
author: Art History Database Team
version: 2.0.0
description: 連接到真實RAG策略服務器的智能組合選擇器
"""

import json
import requests
import asyncio
from typing import List, Dict, Any, Optional, Generator
from pydantic import BaseModel, Field
import time

class Tools:
    def __init__(self):
        self.citation = True
        self.rag_api_url = "http://host.docker.internal:8006"  # 連接到RAG策略服務器

        # 定義RAG+LLM組合（與我們創建的Ollama模型對應）
        self.combos = {
            "llama31-vector-rag": {
                "display": "🔍 Llama 3.1 8B + 向量RAG",
                "strategy": "vector_only",
                "base_model": "llama3.1:8b",
                "description": "語義相似度檢索，適合內容相似性查詢"
            },
            "llama31-graph-rag": {
                "display": "🕸️ Llama 3.1 8B + 圖譜RAG",
                "strategy": "graph_only",
                "base_model": "llama3.1:8b",
                "description": "知識圖譜推理，適合關係和結構化查詢"
            },
            "llama31-hybrid-rag": {
                "display": "⚖️ Llama 3.1 8B + 混合RAG",
                "strategy": "hybrid_balanced",
                "base_model": "llama3.1:8b",
                "description": "平衡混合策略，適合大多數查詢（推薦）"
            },
            "llama31-adaptive-rag": {
                "display": "🧠 Llama 3.1 8B + 自適應RAG",
                "strategy": "adaptive",
                "base_model": "llama3.1:8b",
                "description": "基於歷史性能自動選擇最佳策略"
            },
            "qwen3-vector-rag": {
                "display": "🔍 Qwen3 4B + 向量RAG",
                "strategy": "vector_only",
                "base_model": "qwen3:4b",
                "description": "快速向量檢索，中文表現優秀"
            },
            "qwen3-hybrid-rag": {
                "display": "⚖️ Qwen3 4B + 混合RAG",
                "strategy": "hybrid_balanced",
                "base_model": "qwen3:4b",
                "description": "快速混合檢索，適合日常中文問答"
            }
        }

    def is_rag_service_available(self) -> bool:
        """檢查RAG服務是否可用"""
        try:
            response = requests.get(f"{self.rag_api_url}/health", timeout=5)
            return response.status_code == 200 and response.json().get("rag_system") == "available"
        except:
            return False

    def detect_model_from_request(self, body: dict) -> str:
        """從請求中檢測使用的模型"""
        # 檢查OpenWebUI的模型選擇
        model = body.get("model", "")

        # 如果是我們的RAG組合模型之一
        if model.replace(":latest", "") in self.combos:
            return model.replace(":latest", "")

        # 默認使用混合策略
        return "llama31-hybrid-rag"

    def query_rag_strategy(self, query: str, model_id: str) -> dict:
        """查詢RAG策略服務器"""
        combo = self.combos.get(model_id)
        if not combo:
            return {"error": f"未知模型: {model_id}"}

        try:
            response = requests.post(
                f"{self.rag_api_url}/query",
                json={
                    "query": query,
                    "strategy": combo["strategy"],
                    "base_model": combo["base_model"],
                    "top_k": 5
                },
                timeout=60
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"RAG服務錯誤: {response.status_code}"}

        except requests.exceptions.RequestException as e:
            return {"error": f"連接RAG服務失敗: {str(e)}"}

tools = Tools()

async def main(
    body: dict,
    __user__: dict = None,
    __event_emitter__ = None,
) -> str:
    """
    OpenWebUI主要入口函數
    根據選擇的RAG+LLM組合模型提供智能回答
    """

    try:
        # 獲取用戶消息
        messages = body.get("messages", [])
        if not messages:
            return "🎨 **藝術史RAG+LLM智能助手**\\n\\n請提出您的藝術史問題，我會根據您選擇的模型組合為您提供專業解答。"

        # 提取最新的用戶消息
        user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break

        if not user_message:
            return "請提供您的問題。"

        # 檢測使用的模型組合
        model_id = tools.detect_model_from_request(body)
        combo = tools.combos.get(model_id)

        if not combo:
            return f"❌ 未知的模型組合: {model_id}"

        # 發射狀態事件（如果可用）
        if __event_emitter__:
            await __event_emitter__({
                "type": "status",
                "data": {"description": f"🔍 使用 {combo['display']} 處理查詢中...", "done": False}
            })

        # 檢查RAG服務可用性
        if not tools.is_rag_service_available():
            return f"""❌ **RAG服務暫時不可用**

您選擇的組合: {combo['display']}
策略: {combo['strategy']}
基礎模型: {combo['base_model']}

請稍後再試或聯繫管理員。"""

        # 查詢RAG策略服務器
        if __event_emitter__:
            await __event_emitter__({
                "type": "status",
                "data": {"description": f"🧠 執行 {combo['strategy']} 策略檢索...", "done": False}
            })

        rag_result = tools.query_rag_strategy(user_message, model_id)

        # 檢查查詢結果
        if "error" in rag_result:
            return f"""❌ **查詢處理失敗**

錯誤信息: {rag_result['error']}
使用組合: {combo['display']}

請稍後再試。"""

        # 成功獲得結果
        if __event_emitter__:
            await __event_emitter__({
                "type": "status",
                "data": {"description": "✅ 生成專業回答中...", "done": False}
            })

        answer = rag_result.get("answer", "無法生成回答")
        sources = rag_result.get("sources", [])
        strategy_used = rag_result.get("strategy_used", combo["strategy"])

        # 構建最終回答
        final_answer = f"""{answer}

---

### 📊 **查詢信息**
- **組合**: {combo['display']}
- **RAG策略**: {strategy_used.replace('_', ' ').title()}
- **基礎模型**: {combo['base_model']}
- **檢索來源**: {len(sources)} 個相關資料"""

        if sources and len(sources) > 0:
            final_answer += "\\n\\n### 📚 **參考資料**\\n"
            for i, source in enumerate(sources[:3], 1):
                title = source.get("title", "Unknown")
                final_answer += f"{i}. {title}\\n"

        # 完成狀態事件
        if __event_emitter__:
            await __event_emitter__({
                "type": "status",
                "data": {"description": f"🎉 {combo['display']} 回答完成", "done": True}
            })

        return final_answer

    except Exception as e:
        error_msg = f"""❌ **系統處理異常**

錯誤: {str(e)}

請稍後重試或聯繫支援。"""

        if __event_emitter__:
            await __event_emitter__({
                "type": "status",
                "data": {"description": "❌ 處理失敗", "done": True}
            })

        return error_msg

# OpenWebUI函數定義
def pipe(
    body: dict,
    __user__: dict = None,
    __event_emitter__ = None,
) -> str:
    """OpenWebUI管道函數"""
    return asyncio.run(main(body, __user__, __event_emitter__))