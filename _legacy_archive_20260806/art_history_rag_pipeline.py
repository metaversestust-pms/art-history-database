"""
OpenWebUI Pipeline: 藝術史 RAG+LLM 組合模型
Title: Art History RAG Pipeline
Author: Art History Database Team
Version: 1.0.0
License: MIT
"""

from typing import List, Union, Generator, Iterator
from pydantic import BaseModel
import requests
import os


class Pipeline:
    class Valves(BaseModel):
        """Pipeline 配置"""
        RAG_SERVER_URL: str = "http://localhost:8010"
        OLLAMA_BASE_URL: str = "http://localhost:11434"
        ENABLE_SOURCE_ATTRIBUTION: bool = True
        MAX_SOURCES: int = 3

    def __init__(self):
        self.name = "Art History RAG Pipeline"
        self.valves = self.Valves()

        # LLM 模型映射
        self.llm_models = {
            "gpt-oss-20b": "gpt-oss:20b",
            "deepseek-r1-8b": "deepseek-r1:8b",
            "gemma3-1b": "gemma3:1b",
            "qwen3-4b": "qwen3:4b",
            "llama3-1-8b": "llama3.1:8b",
            # 新增對應
            "llama3.1": "llama3.1:8b",
            "qwen2.5": "qwen2.5:7b",
            "gemma2": "gemma2:2b",
        }

        # RAG 策略映射
        self.rag_strategies = {
            "basic_rag": "hybrid_balanced",
            "advanced_rag": "advanced_rag",
            "vector_rag": "vector_only",
            "graph_rag": "graph_only",
            "agentic_rag": "agentic_rag",
            "self_rag": "self_rag",
            "naive_rag": "naive_rag",
            "enhanced_rag": "enhanced_rag",  # 新增
            "hybrid_rag": "hybrid_balanced",  # 新增
        }

    async def on_startup(self):
        """啟動時的初始化"""
        print(f"🎨 {self.name} 啟動")
        print(f"📡 RAG Server: {self.valves.RAG_SERVER_URL}")
        print(f"🤖 Ollama: {self.valves.OLLAMA_BASE_URL}")

    async def on_shutdown(self):
        """關閉時的清理"""
        print(f"👋 {self.name} 關閉")

    async def inlet(self, body: dict, user: dict) -> dict:
        """請求預處理"""
        print(f"📥 收到請求: {body.get('model', 'unknown')}")
        return body

    def parse_model_name(self, model_name: str) -> dict:
        """
        解析模型名稱
        格式: {llm-model-id}-{rag-strategy-id}
        例如: qwen3-4b-vector_rag -> llm: qwen3:4b, rag: vector_only
        """
        parts = model_name.split('-')

        # 檢查是否是 RAG 組合模型
        if len(parts) < 2:
            return None

        # 嘗試不同的分割方式
        # 格式1: llm-size-rag (如 qwen3-4b-vector_rag)
        if len(parts) >= 3:
            llm_key = f"{parts[0]}-{parts[1]}"  # qwen3-4b
            rag_key = "-".join(parts[2:])  # vector_rag
        # 格式2: llm-rag (如 llama3.1-vector_rag)
        else:
            llm_key = parts[0]  # llama3.1
            rag_key = parts[1]  # vector_rag

        # 查找 LLM 模型
        llm_model = self.llm_models.get(llm_key)
        if not llm_model:
            return None

        # 查找 RAG 策略
        rag_strategy = self.rag_strategies.get(rag_key)
        if not rag_strategy:
            return None

        return {
            "llm_model": llm_model,
            "rag_strategy": rag_strategy,
            "display_name": f"{llm_key} + {rag_key}"
        }

    def query_rag(self, query: str, strategy: str, top_k: int = 5) -> dict:
        """查詢 RAG 系統"""
        try:
            response = requests.post(
                f"{self.valves.RAG_SERVER_URL}/query",
                json={
                    "query": query,
                    "strategy": strategy,
                    "top_k": top_k
                },
                timeout=30
            )

            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"❌ RAG 查詢失敗: {e}")

        return {"sources": [], "context": ""}

    def query_llm(self, model: str, prompt: str, stream: bool = False) -> Union[str, Iterator]:
        """查詢 Ollama LLM"""
        try:
            response = requests.post(
                f"{self.valves.OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": stream,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 2048
                    }
                },
                stream=stream,
                timeout=120
            )

            if stream:
                return self._stream_response(response)
            else:
                if response.status_code == 200:
                    return response.json().get("response", "")
        except Exception as e:
            print(f"❌ LLM 查詢失敗: {e}")

        return "抱歉，生成回答時發生錯誤。"

    def _stream_response(self, response):
        """流式響應生成器"""
        for line in response.iter_lines():
            if line:
                try:
                    import json
                    data = json.loads(line)
                    if "response" in data:
                        yield data["response"]
                except:
                    pass

    def format_sources(self, sources: list, rag_strategy: str, llm_model: str) -> str:
        """格式化來源信息"""
        if not sources or not self.valves.ENABLE_SOURCE_ATTRIBUTION:
            return ""

        result = "\n\n---\n\n"
        result += "📊 **檢索信息**\n"
        result += f"- 🔍 RAG 策略: {rag_strategy}\n"
        result += f"- 🤖 LLM 模型: {llm_model}\n"
        result += f"- 📚 檢索來源: {len(sources)} 個\n\n"

        result += "**參考資料來源:**\n"
        for i, source in enumerate(sources[:self.valves.MAX_SOURCES], 1):
            db = source.get("database", "unknown").upper()
            origin = source.get("source", "Unknown")
            score = source.get("score", 0)
            method = source.get("method", "unknown")

            result += f"{i}. 📊 {db} > {origin}\n"
            result += f"   🎯 相關度: {score:.2f} | 方法: {method}\n"

        return result

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        """主要處理邏輯"""

        print(f"🔍 處理模型: {model_id}")
        print(f"📝 用戶問題: {user_message[:100]}...")

        # 解析模型名稱
        model_info = self.parse_model_name(model_id)

        if not model_info:
            return f"錯誤：無法識別的模型名稱 '{model_id}'。\n\n請使用格式：llm-model-rag-strategy\n例如：qwen3-4b-vector_rag"

        llm_model = model_info["llm_model"]
        rag_strategy = model_info["rag_strategy"]

        print(f"   → LLM: {llm_model}")
        print(f"   → RAG: {rag_strategy}")

        # 1. RAG 檢索
        print("   🔍 執行 RAG 檢索...")
        rag_result = self.query_rag(user_message, rag_strategy)

        sources = rag_result.get("sources", [])
        context = rag_result.get("context", "")

        print(f"   ✅ 檢索到 {len(sources)} 個結果")

        # 2. 構建增強提示詞
        if context and sources:
            enhanced_prompt = f"""基於以下藝術史知識庫資料回答問題：

【參考資料】
{context}

【用戶問題】
{user_message}

【回答要求】
1. 基於上述參考資料回答問題
2. 引用具體的藝術家、作品名稱
3. 保持專業和準確
4. 如果資料不足以回答，請誠實說明

【回答】
"""
        else:
            enhanced_prompt = f"""作為藝術史專家，請回答以下問題：

【用戶問題】
{user_message}

【回答要求】
請提供專業的藝術史解答。

【回答】
"""

        # 3. LLM 生成
        print(f"   🤖 使用 {llm_model} 生成回答...")

        stream = body.get("stream", False)

        if stream:
            # 流式響應
            def response_generator():
                # 先生成 LLM 回答
                for chunk in self.query_llm(llm_model, enhanced_prompt, stream=True):
                    yield chunk

                # 最後添加來源信息
                source_info = self.format_sources(sources, rag_strategy, llm_model)
                if source_info:
                    yield source_info

            return response_generator()
        else:
            # 非流式響應
            answer = self.query_llm(llm_model, enhanced_prompt, stream=False)

            # 添加來源信息
            source_info = self.format_sources(sources, rag_strategy, llm_model)
            final_answer = answer + source_info

            print("   ✅ 生成完成")
            return final_answer
