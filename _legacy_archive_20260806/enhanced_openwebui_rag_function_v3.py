"""
title: 藝術史 RAG+LLM 完整智能組合系統 v3.0
author: Art History Database Team
version: 3.0.0
description: 支援5種LLM模型 × 6種RAG策略的完整組合系統
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
        # 嘗試不同的連接方式，適應不同環境
        import os
        if os.getenv('DOCKER_ENV') == 'true':
            self.rag_api_url = "http://host.docker.internal:8008"
        else:
            self.rag_api_url = "http://localhost:8008"  # 本地測試環境

        # 定義所有LLM模型
        self.llm_models = {
            "gpt-oss:20b": {
                "display_name": "GPT-OSS 20B",
                "description": "開源GPT模型，20B參數，強大的語言理解能力",
                "strengths": ["創意寫作", "複雜推理", "多語言支持"],
                "performance": "high"
            },
            "deepseek-r1:8b": {
                "display_name": "DeepSeek-R1 8B",
                "description": "專注推理的DeepSeek模型，8B參數",
                "strengths": ["邏輯推理", "數學計算", "代碼生成"],
                "performance": "high"
            },
            "gemma3:1b": {
                "display_name": "Gemma3 1B",
                "description": "輕量級Gemma模型，1B參數，快速響應",
                "strengths": ["快速響應", "資源效率", "基礎問答"],
                "performance": "fast"
            },
            "qwen3:4b": {
                "display_name": "Qwen3 4B",
                "description": "阿里巴巴Qwen模型，4B參數，中文優化",
                "strengths": ["中文理解", "文化背景", "平衡性能"],
                "performance": "balanced"
            },
            "llama3.1:8b": {
                "display_name": "Llama 3.1 8B",
                "description": "Meta最新Llama模型，8B參數，全面優化",
                "strengths": ["通用能力", "指令遵循", "安全性"],
                "performance": "balanced"
            }
        }

        # 定義所有RAG策略（映射到後端策略名稱）
        self.rag_strategies = {
            "basic_rag": {
                "display_name": "基礎RAG",
                "backend_strategy": "hybrid_balanced",
                "description": "平衡的混合檢索策略，適合大多數查詢",
                "icon": "⚖️",
                "use_cases": ["通用問答", "基礎檢索", "平衡查詢"]
            },
            "advanced_rag": {
                "display_name": "Advanced RAG",
                "backend_strategy": "advanced_rag",
                "description": "多級檢索與重排序，提供深度分析",
                "icon": "🎯",
                "use_cases": ["複雜分析", "深度研究", "學術查詢"]
            },
            "vector_rag": {
                "display_name": "VectorRAG",
                "backend_strategy": "vector_only",
                "description": "純向量檢索，基於語義相似度",
                "icon": "🔍",
                "use_cases": ["相似內容", "語義搜索", "內容匹配"]
            },
            "graph_rag": {
                "display_name": "GraphRAG",
                "backend_strategy": "graph_only",
                "description": "知識圖譜檢索，探索概念關係",
                "icon": "🕸️",
                "use_cases": ["關係分析", "結構化查詢", "概念探索"]
            },
            "agentic_rag": {
                "display_name": "AgenticRAG",
                "backend_strategy": "agentic_rag",
                "description": "智能代理式推理，多步驟決策",
                "icon": "🤖",
                "use_cases": ["複雜推理", "多步分析", "智能決策"]
            },
            "self_rag": {
                "display_name": "SelfRAG",
                "backend_strategy": "self_rag",
                "description": "自我反思策略，迭代改進答案",
                "icon": "🔄",
                "use_cases": ["質量保證", "自我改進", "準確性驗證"]
            },
            "naive_rag": {
                "display_name": "NaiveRAG",
                "backend_strategy": "naive_rag",
                "description": "最簡單的檢索策略，極速響應",
                "icon": "⚡",
                "use_cases": ["極速查詢", "簡單問答", "基礎匹配"]
            }
        }

        # 生成所有可能的組合
        self.model_combinations = {}
        for model_id, model_info in self.llm_models.items():
            for strategy_id, strategy_info in self.rag_strategies.items():
                combo_id = f"{model_id.replace(':', '-').replace('.', '-')}-{strategy_id}"
                self.model_combinations[combo_id] = {
                    "display": f"{strategy_info['icon']} {model_info['display_name']} + {strategy_info['display_name']}",
                    "model_id": model_id,
                    "strategy_id": strategy_id,
                    "backend_strategy": strategy_info['backend_strategy'],
                    "description": f"{model_info['description']} | {strategy_info['description']}",
                    "performance_level": model_info['performance'],
                    "use_cases": strategy_info['use_cases'],
                    "strengths": model_info['strengths']
                }

    def is_rag_service_available(self) -> bool:
        """檢查RAG服務是否可用"""
        try:
            response = requests.get(f"{self.rag_api_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False

    def get_available_strategies(self) -> List[str]:
        """獲取可用的RAG策略"""
        try:
            response = requests.get(f"{self.rag_api_url}/system/strategies", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [strategy['name'] for strategy in data.get('strategies', [])]
            return []
        except:
            return []

    def detect_model_from_request(self, body: dict) -> str:
        """從請求中檢測使用的模型組合"""
        model = body.get("model", "")

        # 移除可能的 :latest 後綴
        model = model.replace(":latest", "")

        # 檢查是否是我們的組合模型之一
        if model in self.model_combinations:
            return model

        # 如果不是組合模型，嘗試匹配基礎模型
        for combo_id, combo_info in self.model_combinations.items():
            if combo_info['model_id'].replace(':', '-') in model:
                return combo_id

        # 默認使用 llama3.1 + 基礎RAG
        return "llama3-1-8b-basic_rag"

    def query_rag_strategy(self, query: str, combo_id: str) -> dict:
        """查詢RAG策略服務器"""
        combo = self.model_combinations.get(combo_id)
        if not combo:
            return {"error": f"未知模型組合: {combo_id}"}

        try:
            response = requests.post(
                f"{self.rag_api_url}/query",
                json={
                    "query": query,
                    "strategy": combo["backend_strategy"],
                    "top_k": 5,
                    "include_sources": True
                },
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                # 添加模型組合信息到結果中
                result["model_combination"] = {
                    "combo_id": combo_id,
                    "llm_model": combo["model_id"],
                    "rag_strategy": combo["strategy_id"],
                    "display_name": combo["display"]
                }
                return result
            else:
                return {"error": f"RAG服務錯誤: {response.status_code} - {response.text}"}

        except requests.exceptions.RequestException as e:
            return {"error": f"連接RAG服務失敗: {str(e)}"}

    def get_combination_info(self, combo_id: str) -> dict:
        """獲取組合信息"""
        return self.model_combinations.get(combo_id, {})

tools = Tools()

async def main(
    body: dict,
    __user__: dict = None,
    __event_emitter__ = None,
) -> str:
    """
    OpenWebUI主要入口函數
    支援5種LLM模型 × 6種RAG策略 = 30種組合
    """

    try:
        # 獲取用戶消息
        messages = body.get("messages", [])
        if not messages:
            return generate_welcome_message()

        # 提取最新的用戶消息
        user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break

        if not user_message:
            return "請提供您的問題。"

        # 檢測使用的模型組合
        combo_id = tools.detect_model_from_request(body)
        combo_info = tools.get_combination_info(combo_id)

        if not combo_info:
            return f"❌ 未找到模型組合: {combo_id}"

        # 發射狀態事件
        if __event_emitter__:
            await __event_emitter__({
                "type": "status",
                "data": {"description": f"🚀 啟動 {combo_info['display']} 處理中...", "done": False}
            })

        # 檢查RAG服務可用性
        if not tools.is_rag_service_available():
            return generate_service_unavailable_message(combo_info)

        # 查詢RAG策略服務器
        if __event_emitter__:
            await __event_emitter__({
                "type": "status",
                "data": {"description": f"🧠 執行 {combo_info['backend_strategy']} 策略檢索...", "done": False}
            })

        rag_result = tools.query_rag_strategy(user_message, combo_id)

        # 檢查查詢結果
        if "error" in rag_result:
            return generate_error_message(rag_result['error'], combo_info)

        # 成功獲得結果，生成最終回答
        if __event_emitter__:
            await __event_emitter__({
                "type": "status",
                "data": {"description": "✅ 生成專業回答中...", "done": False}
            })

        final_answer = generate_comprehensive_answer(rag_result, combo_info)

        # 完成狀態事件
        if __event_emitter__:
            await __event_emitter__({
                "type": "status",
                "data": {"description": f"🎉 {combo_info['display']} 回答完成", "done": True}
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

def generate_welcome_message() -> str:
    """生成歡迎消息"""
    return """🎨 **藝術史RAG+LLM完整智能組合系統 v3.0**

## 🤖 支援的LLM模型 (5種)
- **GPT-OSS 20B**: 強大的語言理解能力
- **DeepSeek-R1 8B**: 專注推理的模型
- **Gemma3 1B**: 輕量級快速響應
- **Qwen3 4B**: 中文優化平衡性能
- **Llama 3.1 8B**: 全面優化通用能力

## 🔍 支援的RAG策略 (7種)
- **⚖️ 基礎RAG**: 平衡混合策略
- **🎯 Advanced RAG**: 多級檢索與重排序
- **🔍 VectorRAG**: 純向量語義檢索
- **🕸️ GraphRAG**: 知識圖譜關係檢索
- **🤖 AgenticRAG**: 智能代理式推理
- **🔄 SelfRAG**: 自我反思迭代改進
- **⚡ NaiveRAG**: 最簡單策略，極速響應

## 🎯 組合總數: 35種 (5×7)

請在模型選擇中選擇您需要的LLM+RAG組合，然後提出您的藝術史問題！"""

def generate_service_unavailable_message(combo_info: dict) -> str:
    """生成服務不可用消息"""
    return f"""❌ **RAG服務暫時不可用**

您選擇的組合: {combo_info['display']}
- LLM模型: {combo_info['model_id']}
- RAG策略: {combo_info['strategy_id']}
- 性能級別: {combo_info['performance_level']}

請稍後再試或聯繫管理員。"""

def generate_error_message(error: str, combo_info: dict) -> str:
    """生成錯誤消息"""
    return f"""❌ **查詢處理失敗**

錯誤信息: {error}
使用組合: {combo_info['display']}

請稍後再試。"""

def generate_comprehensive_answer(rag_result: dict, combo_info: dict) -> str:
    """生成綜合回答"""
    answer = rag_result.get("answer", "無法生成回答")
    sources = rag_result.get("sources", [])
    strategy_used = rag_result.get("strategy_used", combo_info["backend_strategy"])
    confidence_score = rag_result.get("confidence_score", 0.0)
    processing_time = rag_result.get("processing_time", 0.0)

    # 構建最終回答
    final_answer = f"""{answer}

---

### 📊 **執行信息**
- **🤖 LLM模型**: {combo_info['model_id']} ({tools.llm_models[combo_info['model_id']]['display_name']})
- **🔍 RAG策略**: {combo_info['strategy_id']} → {strategy_used}
- **⚡ 性能級別**: {combo_info['performance_level'].title()}
- **🎯 信心分數**: {confidence_score:.2f}
- **⏱️ 處理時間**: {processing_time:.3f}秒
- **📚 檢索來源**: {len(sources)} 個相關資料"""

    # 添加模型優勢信息
    if combo_info.get('strengths'):
        final_answer += f"\n- **💪 模型優勢**: {', '.join(combo_info['strengths'])}"

    # 添加適用場景
    if combo_info.get('use_cases'):
        final_answer += f"\n- **🎯 適用場景**: {', '.join(combo_info['use_cases'])}"

    # 添加參考資料（如果有的話）
    if sources and len(sources) > 0:
        final_answer += "\n\n### 📚 **參考資料**\n"
        for i, source in enumerate(sources[:3], 1):
            title = source.get("title", source.get("content", "Unknown")[:50] + "...")
            score = source.get("score", 0.0)
            final_answer += f"{i}. {title} (相關度: {score:.2f})\n"

    # 添加特殊策略說明
    strategy_descriptions = {
        "advanced_rag": "📈 採用多級檢索和重排序技術，提供更深度的分析",
        "agentic_rag": "🤖 智能代理進行多步驟推理，確保邏輯連貫性",
        "self_rag": "🔄 自我評估和迭代改進，提高答案質量",
        "graph_rag": "🕸️ 利用知識圖譜挖掘概念間的深層關係",
        "vector_rag": "🔍 基於語義向量進行精確的相似度匹配",
        "naive_rag": "⚡ 採用最簡單的關鍵詞匹配，提供極速響應"
    }

    if combo_info['strategy_id'] in strategy_descriptions:
        final_answer += f"\n\n### 🔬 **策略特色**\n{strategy_descriptions[combo_info['strategy_id']]}"

    return final_answer

# OpenWebUI函數定義
def pipe(
    body: dict,
    __user__: dict = None,
    __event_emitter__ = None,
) -> str:
    """OpenWebUI管道函數"""
    return asyncio.run(main(body, __user__, __event_emitter__))