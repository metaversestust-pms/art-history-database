"""
title: 藝術史 RAG 智能檢索系統
author: Art History Database Team
version: 3.1.0
required_open_webui_version: 0.3.0
"""

import json
import requests
from typing import Optional, Callable, Any
from pydantic import BaseModel, Field


class Function:
    """OpenWebUI Function類 - 連接RAG Manager後端"""

    def __init__(self):
        # RAG Manager API配置（自動檢測端口8007）
        self.rag_api_url = "http://localhost:8007"

        # 模型與策略映射
        self.rag_models_mapping = {
            "llama31-vector-rag": {"model": "llama3.1:8b", "strategy": "vector_only"},
            "llama31-graph-rag": {"model": "llama3.1:8b", "strategy": "graph_only"},
            "llama31-hybrid-rag": {"model": "llama3.1:8b", "strategy": "hybrid_balanced"},
            "qwen3-vector-rag": {"model": "qwen3:4b", "strategy": "vector_only"},
            "qwen3-hybrid-rag": {"model": "qwen3:4b", "strategy": "hybrid_balanced"},
            "qwen3-8b-graph-rag": {"model": "qwen3:8b", "strategy": "graph_only"},
        }

    class Valves(BaseModel):
        """可配置參數"""
        RAG_API_URL: str = Field(
            default="http://localhost:8007",
            description="RAG Manager API端點"
        )
        ENABLE_STATUS_MESSAGES: bool = Field(
            default=True,
            description="啟用狀態消息"
        )
        TOP_K: int = Field(
            default=5,
            description="檢索結果數量"
        )
        TIMEOUT: int = Field(
            default=60,
            description="API請求超時時間（秒）"
        )

    def __init__(self):
        self.valves = self.Valves()

    async def inlet(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __event_emitter__: Optional[Callable[[dict], Any]] = None,
    ) -> dict:
        """
        處理進入的請求

        此inlet函數會在消息發送到LLM之前執行，用於：
        1. 檢測使用的RAG模型
        2. 調用RAG Manager檢索相關資料
        3. 將檢索結果注入到上下文中
        """

        # 提取用戶消息
        messages = body.get("messages", [])
        if not messages:
            return body

        user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break

        if not user_message:
            return body

        # 檢測使用的模型
        model_name = body.get("model", "")

        # 發送狀態消息
        if __event_emitter__ and self.valves.ENABLE_STATUS_MESSAGES:
            await __event_emitter__({
                "type": "status",
                "data": {
                    "description": f"🔍 檢測到模型: {model_name}",
                    "done": False
                }
            })

        # 檢查是否是RAG組合模型
        model_config = None
        for rag_model, config in self.rag_models_mapping.items():
            if rag_model in model_name:
                model_config = config
                break

        # 如果不是RAG模型，直接返回
        if not model_config:
            return body

        # 調用RAG Manager
        if __event_emitter__ and self.valves.ENABLE_STATUS_MESSAGES:
            await __event_emitter__({
                "type": "status",
                "data": {
                    "description": f"🧠 執行RAG檢索: {model_config['strategy']}",
                    "done": False
                }
            })

        rag_result = self._query_rag_manager(
            user_message,
            model_config['model'],
            model_config['strategy']
        )

        # 檢查結果
        if "error" in rag_result:
            # 如果RAG失敗，添加錯誤提示但繼續執行
            system_message = f"⚠️ RAG檢索失敗: {rag_result['error']}\n\n將使用基礎模型回答。"
            messages.insert(0, {
                "role": "system",
                "content": system_message
            })
            body["messages"] = messages

            if __event_emitter__:
                await __event_emitter__({
                    "type": "status",
                    "data": {
                        "description": "⚠️ RAG檢索失敗，使用基礎模型",
                        "done": True
                    }
                })

            return body

        # RAG成功，注入檢索結果
        answer = rag_result.get("answer", "")
        sources = rag_result.get("sources", [])
        metadata = rag_result.get("metadata", {})

        # 構建增強的系統提示
        context_text = self._build_context(answer, sources, metadata, model_config)

        # 將context注入到系統消息中
        system_message = {
            "role": "system",
            "content": context_text
        }

        # 插入到消息列表開頭
        messages.insert(0, system_message)
        body["messages"] = messages

        if __event_emitter__ and self.valves.ENABLE_STATUS_MESSAGES:
            await __event_emitter__({
                "type": "status",
                "data": {
                    "description": f"✅ RAG檢索完成 ({len(sources)} 個來源)",
                    "done": True
                }
            })

        return body

    def _query_rag_manager(self, query: str, model: str, strategy: str) -> dict:
        """查詢RAG Manager API"""
        try:
            # 構建API請求
            api_url = f"{self.valves.RAG_API_URL}/api/v1/query"

            # 根據策略選擇model_combination_id格式
            model_combination_id = f"{model}@{strategy}"

            payload = {
                "query": query,
                "model_combination_id": model_combination_id,
                "top_k": self.valves.TOP_K
            }

            response = requests.post(
                api_url,
                json=payload,
                timeout=self.valves.TIMEOUT
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API返回錯誤: {response.status_code}"}

        except requests.exceptions.ConnectionError:
            return {"error": "無法連接到RAG Manager (http://localhost:8007)"}
        except requests.exceptions.Timeout:
            return {"error": "RAG Manager請求超時"}
        except Exception as e:
            return {"error": f"未知錯誤: {str(e)}"}

    def _build_context(self, answer: str, sources: list, metadata: dict, model_config: dict) -> str:
        """構建context文本"""
        context = f"""🎨 **藝術史RAG檢索結果**

**檢索配置**:
- 基礎模型: {model_config['model']}
- RAG策略: {model_config['strategy']}
- 檢索來源: {len(sources)} 個相關資料

**RAG檢索回答**:
{answer}

"""

        # 添加來源信息
        if sources:
            context += "**參考資料**:\n"
            for i, source in enumerate(sources[:3], 1):
                content = source.get("content", "")[:100]
                score = source.get("score", 0.0)
                context += f"{i}. {content}... (相關度: {score:.2f})\n"

        context += "\n請基於以上RAG檢索結果，用專業、準確的方式回答用戶的問題。"

        return context
