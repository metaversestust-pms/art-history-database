"""
title: 藝術史 RAG+LLM 組合選擇器
author: Art History Database Team
version: 1.0.0
description: 在OpenWebUI中提供RAG策略+LLM模型組合選擇功能
"""

import json
import requests
import asyncio
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class RAGModelCombo(BaseModel):
    id: str = Field(..., description="組合ID")
    name: str = Field(..., description="顯示名稱")
    description: str = Field(..., description="描述")
    base_model: str = Field(..., description="基礎LLM模型")
    rag_strategy: str = Field(..., description="RAG策略")
    temperature: float = Field(0.1, description="溫度參數")
    max_tokens: int = Field(2048, description="最大token數")


class Tools:
    def __init__(self):
        self.citation = True

        # 定義RAG+LLM組合
        self.rag_combos = [
            RAGModelCombo(
                id="llama3.1_vector",
                name="🔍 Llama 3.1 8B + 向量RAG",
                description="語義相似度檢索，適合內容相似性查詢",
                base_model="llama3.1:8b",
                rag_strategy="vector_only",
                temperature=0.1,
                max_tokens=2048
            ),
            RAGModelCombo(
                id="llama3.1_graph",
                name="🕸️ Llama 3.1 8B + 圖譜RAG",
                description="知識圖譜推理，適合關係和結構化查詢",
                base_model="llama3.1:8b",
                rag_strategy="graph_only",
                temperature=0.1,
                max_tokens=2048
            ),
            RAGModelCombo(
                id="llama3.1_hybrid",
                name="⚖️ Llama 3.1 8B + 混合RAG",
                description="平衡混合策略，適合大多數查詢（推薦）",
                base_model="llama3.1:8b",
                rag_strategy="hybrid_balanced",
                temperature=0.1,
                max_tokens=2048
            ),
            RAGModelCombo(
                id="llama3.1_adaptive",
                name="🧠 Llama 3.1 8B + 自適應RAG",
                description="基於歷史性能自動選擇最佳策略",
                base_model="llama3.1:8b",
                rag_strategy="adaptive",
                temperature=0.1,
                max_tokens=2048
            ),
            RAGModelCombo(
                id="llama3.1_specialized",
                name="🎯 Llama 3.1 8B + 專門RAG",
                description="基於查詢類型自動選擇專門策略",
                base_model="llama3.1:8b",
                rag_strategy="specialized",
                temperature=0.1,
                max_tokens=2048
            ),
            RAGModelCombo(
                id="qwen3_vector",
                name="🔍 Qwen3 4B + 向量RAG",
                description="快速向量檢索，中文表現優秀",
                base_model="qwen3:4b",
                rag_strategy="vector_only",
                temperature=0.2,
                max_tokens=1500
            ),
            RAGModelCombo(
                id="qwen3_hybrid",
                name="⚖️ Qwen3 4B + 混合RAG",
                description="快速混合檢索，適合日常中文問答",
                base_model="qwen3:4b",
                rag_strategy="hybrid_balanced",
                temperature=0.2,
                max_tokens=1500
            ),
            RAGModelCombo(
                id="llama3.1_pure",
                name="💬 Llama 3.1 8B (純模型)",
                description="不使用RAG，僅基於預訓練知識",
                base_model="llama3.1:8b",
                rag_strategy="none",
                temperature=0.3,
                max_tokens=2048
            ),
            RAGModelCombo(
                id="qwen3_pure",
                name="💬 Qwen3 4B (純模型)",
                description="不使用RAG，快速基礎對話",
                base_model="qwen3:4b",
                rag_strategy="none",
                temperature=0.4,
                max_tokens=1500
            )
        ]

        self.rag_api_url = "http://host.docker.internal:8002"
        self.ollama_api_url = "http://host.docker.internal:11434"

    def get_rag_combos(self) -> List[Dict[str, Any]]:
        """獲取所有RAG+LLM組合列表"""
        return [combo.dict() for combo in self.rag_combos]

    def find_combo(self, combo_id: str) -> Optional[RAGModelCombo]:
        """根據ID查找組合"""
        for combo in self.rag_combos:
            if combo.id == combo_id:
                return combo
        return None

    def query_with_rag(self, query: str, rag_strategy: str, top_k: int = 5) -> Optional[str]:
        """使用RAG增強查詢"""
        if rag_strategy == "none":
            return query

        try:
            response = requests.post(
                f"{self.rag_api_url}/query",
                json={
                    "query": query,
                    "strategy": rag_strategy,
                    "top_k": top_k,
                    "include_sources": True
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()

                # 構建增強提示詞
                context = ""
                if result.get("sources"):
                    context = "\\n\\n相關藝術史資料：\\n"
                    for i, source in enumerate(result["sources"][:3], 1):
                        title = source.get("title", "Unknown")
                        content = source.get("content", "")[:200] + "..."
                        context += f"{i}. {title}: {content}\\n"

                enhanced_prompt = f"""基於以下藝術史知識庫資料回答問題：

{context}

問題：{query}

請基於上述資料提供專業的藝術史解答，如果資料不足，請說明並提供一般性建議。"""

                return enhanced_prompt

        except Exception as e:
            print(f"RAG查詢失敗: {e}")

        return query

    def query_ollama(self, model: str, prompt: str, temperature: float = 0.1, max_tokens: int = 2048) -> str:
        """查詢Ollama模型"""
        try:
            response = requests.post(
                f"{self.ollama_api_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens
                    }
                },
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")

        except Exception as e:
            print(f"Ollama查詢失敗: {e}")

        return "抱歉，查詢處理失敗，請稍後再試。"


# 實例化工具
tools = Tools()


def list_rag_combos() -> str:
    """
    列出所有可用的RAG+LLM組合

    Returns:
        str: 格式化的組合列表
    """
    combo_list = tools.get_rag_combos()

    result = "🎨 **可用的RAG+LLM組合：**\\n\\n"

    for i, combo in enumerate(combo_list, 1):
        result += f"{i}. **{combo['name']}**\\n"
        result += f"   - ID: `{combo['id']}`\\n"
        result += f"   - 描述: {combo['description']}\\n"
        result += f"   - 基礎模型: {combo['base_model']}\\n"
        result += f"   - RAG策略: {combo['rag_strategy']}\\n\\n"

    result += "💡 **使用方式：** 請告訴我您想使用哪個組合ID，或直接提問題讓我使用推薦組合回答。"

    return result


def query_with_combo(
    query: str,
    combo_id: str = "llama3.1_hybrid",
    __user__: dict = None,
    __event_emitter__ = None
) -> str:
    """
    使用指定的RAG+LLM組合回答問題

    Args:
        query (str): 用戶查詢
        combo_id (str): RAG+LLM組合ID (預設: llama3.1_hybrid)

    Returns:
        str: AI回答
    """
    # 查找組合
    combo = tools.find_combo(combo_id)
    if not combo:
        available_ids = [c.id for c in tools.rag_combos]
        return f"❌ 找不到組合ID: {combo_id}\\n\\n可用ID: {', '.join(available_ids)}"

    try:
        # RAG增強查詢
        enhanced_query = tools.query_with_rag(query, combo.rag_strategy)

        # LLM生成回答
        response = tools.query_ollama(
            combo.base_model,
            enhanced_query,
            combo.temperature,
            combo.max_tokens
        )

        # 添加策略資訊
        strategy_info = f"\\n\\n---\\n🔧 **使用組合:** {combo.name}\\n📊 **RAG策略:** {combo.rag_strategy.replace('_', ' ').title()}"

        return response + strategy_info

    except Exception as e:
        return f"❌ 查詢處理失敗: {str(e)}"


async def main(
    body: dict,
    __user__: dict = None,
    __event_emitter__ = None,
) -> str:
    """
    OpenWebUI主要入口函數
    自動處理用戶查詢並使用最佳RAG+LLM組合
    """
    try:
        messages = body.get("messages", [])

        if not messages:
            return list_rag_combos()

        # 獲取最新用戶消息
        user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break

        if not user_message:
            return list_rag_combos()

        # 檢查是否是列表查詢
        list_keywords = ["組合", "combo", "選項", "list", "列表", "可用"]
        if any(keyword in user_message.lower() for keyword in list_keywords):
            return list_rag_combos()

        # 智能選擇RAG組合
        combo_id = "llama3.1_hybrid"  # 預設使用混合策略

        # 根據查詢內容選擇合適組合
        if any(keyword in user_message for keyword in ["相似", "像", "風格"]):
            combo_id = "llama3.1_vector"  # 向量檢索
        elif any(keyword in user_message for keyword in ["關係", "影響", "師徒", "學派"]):
            combo_id = "llama3.1_graph"   # 圖譜推理
        elif any(keyword in user_message for keyword in ["快速", "簡單"]):
            combo_id = "qwen3_hybrid"     # 快速回答

        # 使用選定組合處理查詢
        return query_with_combo(user_message, combo_id, __user__, __event_emitter__)

    except Exception as e:
        return f"❌ 函數執行失敗: {str(e)}\\n\\n" + list_rag_combos()


# OpenWebUI函數定義
def pipe(
    body: dict,
    __user__: dict = None,
    __event_emitter__ = None,
) -> str:
    """OpenWebUI管道函數"""
    return asyncio.run(main(body, __user__, __event_emitter__))