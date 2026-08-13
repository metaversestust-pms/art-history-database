"""
title: 藝術史 RAG+LLM 完整智能組合系統 v5.0 - 大型模型擴展版
author: Art History Database Team
version: 5.0.0
description: 支援9種LLM模型 × 8種RAG策略，整合Neo4j+ChromaDB雙資料庫。新增大型高性能模型！
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
        # 支持三服務器配置（標準、增強、多資料庫）
        import os
        if os.getenv('DOCKER_ENV') == 'true':
            self.rag_api_url = "http://host.docker.internal:8008"  # 標準服務器
            self.enhanced_api_url = "http://host.docker.internal:8009"  # 增強服務器
            self.multidb_api_url = "http://host.docker.internal:8010"  # 多資料庫服務器
        else:
            self.rag_api_url = "http://localhost:8008"  # 標準服務器
            self.enhanced_api_url = "http://localhost:8009"  # 增強服務器
            self.multidb_api_url = "http://localhost:8010"  # 多資料庫服務器

        # 定義所有LLM模型（包含新增的大型模型）
        self.llm_models = {
            # 原有模型
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
            },
            # 🆕 新增大型高性能模型
            "qwen3:30b": {
                "display_name": "🆕 Qwen3 30B",
                "description": "阿里巴巴Qwen超大型模型，30B參數，頂級中文理解",
                "strengths": ["頂級中文理解", "深度文化背景", "複雜推理", "專業寫作"],
                "performance": "ultra-high"
            },
            "deepseek-r1:32b": {
                "display_name": "🆕 DeepSeek-R1 32B",
                "description": "DeepSeek旗艦推理模型，32B參數，極致邏輯推理",
                "strengths": ["極致邏輯推理", "複雜數學", "高級代碼生成", "學術分析"],
                "performance": "ultra-high"
            },
            "llama3.1:70b": {
                "display_name": "🆕 Llama 3.1 70B",
                "description": "Meta旗艦級Llama模型，70B參數，頂級全能表現",
                "strengths": ["頂級通用能力", "複雜指令遵循", "多領域專家", "創意生成"],
                "performance": "ultra-high"
            }
        }

        # 定義所有RAG策略（整合多資料庫支援）
        self.rag_strategies = {
            "enhanced_rag": {
                "display_name": "🚀 Enhanced RAG (Neo4j+ChromaDB)",
                "backend_strategy": "enhanced_rag",
                "description": "增強型檢索：向量+全文+圖譜混合，支持重排序",
                "icon": "🚀",
                "use_cases": ["精確查詢", "語義搜索", "混合檢索"],
                "use_multidb_server": True,
                "primary_database": "neo4j+chromadb",
                "is_new": False
            },
            "hybrid_balanced": {
                "display_name": "⚖️ Hybrid RAG (Neo4j+ChromaDB)",
                "backend_strategy": "hybrid_balanced",
                "description": "平衡混合策略：向量+全文混合檢索",
                "icon": "⚖️",
                "use_cases": ["通用問答", "平衡查詢", "標準檢索"],
                "use_multidb_server": True,
                "primary_database": "neo4j+chromadb",
                "is_new": False
            },
            "vector_only": {
                "display_name": "🔍 Vector RAG (ChromaDB優先)",
                "backend_strategy": "vector_only",
                "description": "純向量檢索，優先使用ChromaDB（1,441作品，95.5%中文標籤）",
                "icon": "🔍",
                "use_cases": ["相似內容", "語義搜索", "中文查詢"],
                "use_multidb_server": True,
                "primary_database": "chromadb",
                "is_new": True
            },
            "graph_only": {
                "display_name": "🕸️ Graph RAG (Neo4j)",
                "backend_strategy": "graph_only",
                "description": "知識圖譜檢索，探索概念關係",
                "icon": "🕸️",
                "use_cases": ["關係分析", "結構化查詢", "概念探索"],
                "use_multidb_server": True,
                "primary_database": "neo4j",
                "is_new": False
            },
            "advanced_rag": {
                "display_name": "🎯 Advanced RAG (ChromaDB優先)",
                "backend_strategy": "advanced_rag",
                "description": "多級檢索與重排序，優先使用ChromaDB",
                "icon": "🎯",
                "use_cases": ["複雜分析", "深度研究", "學術查詢"],
                "use_multidb_server": True,
                "primary_database": "chromadb",
                "is_new": True
            },
            "agentic_rag": {
                "display_name": "🤖 Agentic RAG (ChromaDB優先)",
                "backend_strategy": "agentic_rag",
                "description": "智能代理式推理，優先使用ChromaDB快速向量檢索",
                "icon": "🤖",
                "use_cases": ["複雜推理", "多步分析", "智能決策"],
                "use_multidb_server": True,
                "primary_database": "chromadb",
                "is_new": True
            },
            "self_rag": {
                "display_name": "🔄 Self RAG (ChromaDB優先)",
                "backend_strategy": "self_rag",
                "description": "自我反思策略，優先使用ChromaDB向量反思",
                "icon": "🔄",
                "use_cases": ["質量保證", "自我改進", "準確性驗證"],
                "use_multidb_server": True,
                "primary_database": "chromadb",
                "is_new": True
            },
            "naive_rag": {
                "display_name": "⚡ Naive RAG (ChromaDB)",
                "backend_strategy": "naive_rag",
                "description": "最簡單的檢索策略，只使用ChromaDB極速響應",
                "icon": "⚡",
                "use_cases": ["極速查詢", "簡單問答", "基礎匹配"],
                "use_multidb_server": True,
                "primary_database": "chromadb",
                "is_new": True
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
                    "strengths": model_info['strengths'],
                    "use_multidb_server": strategy_info.get('use_multidb_server', False),
                    "primary_database": strategy_info.get('primary_database', 'neo4j'),
                    "is_new": strategy_info.get('is_new', False)
                }

    def is_service_available(self, url: str) -> bool:
        """檢查服務是否可用"""
        try:
            response = requests.get(f"{url}/health", timeout=3)
            return response.status_code == 200
        except:
            return False

    def get_best_available_server(self, use_multidb: bool = False, use_enhanced: bool = False) -> str:
        """獲取最佳可用服務器"""
        # 優先使用多資料庫服務器（如果策略需要）
        if use_multidb and self.is_service_available(self.multidb_api_url):
            return self.multidb_api_url
        # 其次嘗試增強服務器
        elif use_enhanced and self.is_service_available(self.enhanced_api_url):
            return self.enhanced_api_url
        # 最後使用標準服務器
        elif self.is_service_available(self.rag_api_url):
            return self.rag_api_url
        return None

    def detect_model_from_request(self, body: dict) -> str:
        """從請求中檢測使用的模型組合"""
        model = body.get("model", "").replace(":latest", "")

        if model in self.model_combinations:
            return model

        for combo_id, combo_info in self.model_combinations.items():
            if combo_info['model_id'].replace(':', '-') in model:
                return combo_id

        # 默認使用 llama3.1:70b + Enhanced RAG（新默認！使用最強模型）
        return "llama3-1-70b-enhanced_rag"

    def query_rag_strategy(self, query: str, combo_id: str) -> dict:
        """查詢RAG策略服務器"""
        combo = self.model_combinations.get(combo_id)
        if not combo:
            return {"error": f"未知模型組合: {combo_id}"}

        # 選擇合適的服務器（優先多資料庫服務器）
        server_url = self.get_best_available_server(
            use_multidb=combo.get('use_multidb_server', False),
            use_enhanced=combo.get('use_enhanced_server', False)
        )

        if not server_url:
            return {"error": "所有RAG服務器均不可用"}

        try:
            response = requests.post(
                f"{server_url}/query",
                json={
                    "query": query,
                    "strategy": combo["backend_strategy"],
                    "base_model": combo.get("model_id", ""),
                    "top_k": 5
                },
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                result["model_combination"] = {
                    "combo_id": combo_id,
                    "llm_model": combo["model_id"],
                    "rag_strategy": combo["strategy_id"],
                    "display_name": combo["display"],
                    "server_used": server_url,
                    "primary_database": combo.get('primary_database', 'neo4j'),
                    "uses_multidb": combo.get('use_multidb_server', False)
                }
                return result
            else:
                return {"error": f"RAG服務錯誤: {response.status_code}"}

        except requests.exceptions.RequestException as e:
            return {"error": f"連接失敗: {str(e)}"}

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
    OpenWebUI主要入口函數 v5.0
    支援9種LLM × 8種RAG = 72種組合
    """
    try:
        messages = body.get("messages", [])
        if not messages:
            return generate_welcome_message()

        user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break

        if not user_message:
            return "請提供您的問題。"

        combo_id = tools.detect_model_from_request(body)
        combo_info = tools.get_combination_info(combo_id)

        if not combo_info:
            return f"❌ 未找到模型組合: {combo_id}"

        # 狀態提示
        if __event_emitter__:
            is_new = combo_info.get('is_new', False)
            is_ultra = combo_info.get('performance_level') == 'ultra-high'
            status_prefix = "⚡ " if is_ultra else ("🆕 " if is_new else "🚀 ")
            await __event_emitter__({
                "type": "status",
                "data": {"description": f"{status_prefix}啟動 {combo_info['display']}...", "done": False}
            })

        # 檢查服務可用性
        server_url = tools.get_best_available_server(
            use_multidb=combo_info.get('use_multidb_server', False),
            use_enhanced=combo_info.get('use_enhanced_server', False)
        )
        if not server_url:
            return generate_service_unavailable_message(combo_info)

        # 執行檢索
        if __event_emitter__:
            server_type = "多資料庫" if combo_info.get('use_multidb_server') else ("增強型" if combo_info.get('use_enhanced_server') else "標準")
            db_info = combo_info.get('primary_database', 'neo4j')
            await __event_emitter__({
                "type": "status",
                "data": {"description": f"🧠 執行{server_type}檢索 ({db_info}): {combo_info['backend_strategy']}...", "done": False}
            })

        rag_result = tools.query_rag_strategy(user_message, combo_id)

        if "error" in rag_result:
            return generate_error_message(rag_result['error'], combo_info)

        if __event_emitter__:
            await __event_emitter__({
                "type": "status",
                "data": {"description": "✅ 生成專業回答中...", "done": False}
            })

        final_answer = generate_comprehensive_answer(rag_result, combo_info)

        if __event_emitter__:
            await __event_emitter__({
                "type": "status",
                "data": {"description": f"🎉 {combo_info['display']} 完成", "done": True}
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
    """生成歡迎消息 v5.0"""
    return """🎨 **藝術史RAG+LLM完整智能組合系統 v5.0** 🆕

## ⚡ 新版本亮點
- **🆕 新增3個大型高性能模型**: Qwen3 30B、DeepSeek-R1 32B、Llama 3.1 70B
- **🚀 72種智能組合**: 9種LLM × 8種RAG策略
- **💪 Ultra-High性能等級**: 頂級模型適合複雜任務
- **📊 雙資料庫架構**: Neo4j+ChromaDB協同工作

## 🤖 支援的LLM模型 (9種)

### 🔥 超大型旗艦模型 (NEW!)
- **🆕 Llama 3.1 70B**: 70B參數，Meta旗艦級，頂級全能表現
- **🆕 DeepSeek-R1 32B**: 32B參數，極致邏輯推理與學術分析
- **🆕 Qwen3 30B**: 30B參數，頂級中文理解與文化背景

### 高性能模型
- **GPT-OSS 20B**: 強大的語言理解能力
- **DeepSeek-R1 8B**: 專注推理的模型

### 平衡性能模型
- **Llama 3.1 8B**: 全面優化通用能力
- **Qwen3 4B**: 中文優化平衡性能

### 輕量快速模型
- **Gemma3 1B**: 輕量級快速響應

## 🔍 支援的RAG策略 (8種)
- **🚀 Enhanced RAG**: 增強型混合檢索+重排序
- **⚖️ Hybrid RAG**: 平衡混合策略
- **🔍 Vector RAG**: ChromaDB優先純向量檢索
- **🕸️ Graph RAG**: Neo4j知識圖譜關係檢索
- **🎯 Advanced RAG**: 多級檢索與重排序
- **🤖 Agentic RAG**: 智能代理式推理
- **🔄 Self RAG**: 自我反思迭代改進
- **⚡ Naive RAG**: 極速響應

## 🎯 組合總數: 72種 (9×8)

**🔥 推薦旗艦組合**:
- ⚡ **Llama 3.1 70B + Enhanced RAG** - 最強綜合能力
- 🎓 **DeepSeek-R1 32B + Advanced RAG** - 學術深度分析
- 🇨🇳 **Qwen3 30B + Vector RAG** - 頂級中文理解

**⚡ 推薦平衡組合**:
- 🚀 Llama 3.1 8B + Enhanced RAG (默認)
- 🎯 DeepSeek-R1 8B + Advanced RAG
- 💨 Gemma3 1B + Naive RAG (極速)

請在模型選擇中選擇您需要的LLM+RAG組合，然後提出您的藝術史問題！"""

def generate_service_unavailable_message(combo_info: dict) -> str:
    """生成服務不可用消息"""
    return f"""❌ **RAG服務暫時不可用**

您選擇的組合: {combo_info['display']}
- LLM模型: {combo_info['model_id']}
- RAG策略: {combo_info['strategy_id']}
- 需要多資料庫服務器: {'是' if combo_info.get('use_multidb_server') else '否'}

請確認：
1. RAG服務器正在運行（端口 8008 或 8010）
2. 網絡連接正常

請稍後再試或聯繫管理員。"""

def generate_error_message(error: str, combo_info: dict) -> str:
    """生成錯誤消息"""
    return f"""❌ **查詢處理失敗**

錯誤信息: {error}
使用組合: {combo_info['display']}

請稍後再試。"""

def generate_comprehensive_answer(rag_result: dict, combo_info: dict) -> str:
    """生成綜合回答 v5.0"""
    answer = rag_result.get("answer", "無法生成回答")
    sources = rag_result.get("sources", [])
    metadata = rag_result.get("metadata", {})
    model_combination = rag_result.get("model_combination", {})

    # 檢查是否使用了增強服務器
    is_enhanced = model_combination.get('is_enhanced', False)
    server_used = model_combination.get('server_used', 'unknown')

    # 構建最終回答
    uses_multidb = model_combination.get('uses_multidb', False)
    primary_db = model_combination.get('primary_database', 'neo4j')

    # 判斷是否為超大型模型
    is_ultra = combo_info.get('performance_level') == 'ultra-high'

    # 統計資料來源
    source_stats = {}
    for source in sources:
        db = source.get('source_database', 'unknown')
        source_stats[db] = source_stats.get(db, 0) + 1

    final_answer = f"""{answer}

---

### 📊 **執行信息** {'⚡ ULTRA-HIGH' if is_ultra else ('🆕' if combo_info.get('is_new') else '')}
- **🤖 LLM模型**: {combo_info['model_id']} ({tools.llm_models[combo_info['model_id']]['display_name']})
- **🔍 RAG策略**: {combo_info['strategy_id']} → {combo_info['backend_strategy']}
- **🌐 服務器**: {'多資料庫 (port 8010)' if uses_multidb else ('增強型 (port 8009)' if is_enhanced else '標準 (port 8008)')}
- **💾 主要資料庫**: {primary_db.upper()}
- **⚡ 性能級別**: {combo_info['performance_level'].upper().replace('-', ' ')}
- **📚 檢索來源**: {len(sources)} 個相關資料"""

    # 添加資料來源分布
    if source_stats and uses_multidb:
        stats_str = ", ".join([f"{db}: {count}個" for db, count in source_stats.items()])
        final_answer += f"\n- **📊 資料源分布**: {stats_str}"

    # 添加檢索詳情（如果有）
    if metadata:
        retrieval_time = metadata.get('retrieval_time', 0)
        if retrieval_time > 0:
            final_answer += f"\n- **⏱️ 檢索時間**: {retrieval_time:.3f}秒"

        enhanced_features = metadata.get('enhanced_features', {})
        if enhanced_features:
            features_used = []
            if enhanced_features.get('vector_search'): features_used.append("向量搜索")
            if enhanced_features.get('fulltext_search'): features_used.append("全文搜索")
            if enhanced_features.get('graph_search'): features_used.append("圖譜搜索")
            if enhanced_features.get('reranking'): features_used.append("重排序")
            if features_used:
                final_answer += f"\n- **🔧 使用功能**: {', '.join(features_used)}"

    # 添加模型優勢
    if combo_info.get('strengths'):
        final_answer += f"\n- **💪 模型優勢**: {', '.join(combo_info['strengths'])}"

    # 添加適用場景
    if combo_info.get('use_cases'):
        final_answer += f"\n- **🎯 適用場景**: {', '.join(combo_info['use_cases'])}"

    # 添加參考資料（含來源追蹤）
    if sources and len(sources) > 0:
        final_answer += "\n\n### 📚 **參考資料**\n"
        for i, source in enumerate(sources[:5], 1):
            content = source.get("content", "")[:100]
            score = source.get("score", 0.0)
            method = source.get("retrieval_method", "unknown")
            source_db = source.get("source_database", "unknown")
            original_source = source.get("original_source", "Unknown")

            final_answer += f"\n**[{i}]** {content}...\n"
            final_answer += f"   📊 來源: {source_db.upper()} > {original_source}\n"
            final_answer += f"   🎯 相關度: {score:.2f} | 檢索方法: {method}\n"

    return final_answer

# OpenWebUI函數定義
def pipe(
    body: dict,
    __user__: dict = None,
    __event_emitter__ = None,
) -> str:
    """OpenWebUI管道函數 v5.0"""
    return asyncio.run(main(body, __user__, __event_emitter__))
