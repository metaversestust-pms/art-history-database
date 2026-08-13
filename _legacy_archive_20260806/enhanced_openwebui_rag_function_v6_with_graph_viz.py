"""
title: 藝術史 RAG+LLM 完整智能組合系統 v6.0 - 圖譜視覺化版
author: Art History Database Team
version: 6.0.0
description: 支援9種LLM模型 × 8種RAG策略 + Neo4j圖譜視覺化顯示
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
        # 服務器配置
        import os
        if os.getenv('DOCKER_ENV') == 'true':
            self.rag_api_url = "http://host.docker.internal:8008"
            self.enhanced_api_url = "http://host.docker.internal:8009"
            self.multidb_api_url = "http://host.docker.internal:8010"
            self.neo4j_url = "http://host.docker.internal:7474"
        else:
            self.rag_api_url = "http://localhost:8008"
            self.enhanced_api_url = "http://localhost:8009"
            self.multidb_api_url = "http://localhost:8010"
            self.neo4j_url = "http://localhost:7474"

        self.neo4j_auth = ("neo4j", "arthistory123")  # 根據您的實際配置調整

        # LLM模型定義 (保持原有配置)
        self.llm_models = {
            "gpt-oss:20b": {"display_name": "GPT-OSS 20B", "performance": "high"},
            "deepseek-r1:8b": {"display_name": "DeepSeek-R1 8B", "performance": "high"},
            "gemma3:1b": {"display_name": "Gemma3 1B", "performance": "fast"},
            "qwen3:4b": {"display_name": "Qwen3 4B", "performance": "balanced"},
            "llama3.1:8b": {"display_name": "Llama 3.1 8B", "performance": "balanced"},
            "qwen3:30b": {"display_name": "🆕 Qwen3 30B", "performance": "ultra-high"},
            "deepseek-r1:32b": {"display_name": "🆕 DeepSeek-R1 32B", "performance": "ultra-high"},
            "llama3.1:70b": {"display_name": "🆕 Llama 3.1 70B", "performance": "ultra-high"}
        }

        # RAG策略定義
        self.rag_strategies = {
            "enhanced_rag": {
                "display_name": "🚀 Enhanced RAG (Neo4j+ChromaDB)",
                "backend_strategy": "enhanced_rag",
                "icon": "🚀",
                "use_multidb_server": True,
                "show_graph": True  # 顯示圖譜
            },
            "graph_only": {
                "display_name": "🕸️ Graph RAG (Neo4j)",
                "backend_strategy": "graph_only",
                "icon": "🕸️",
                "use_multidb_server": True,
                "show_graph": True  # 顯示圖譜
            },
            "hybrid_balanced": {
                "display_name": "⚖️ Hybrid RAG",
                "backend_strategy": "hybrid_balanced",
                "icon": "⚖️",
                "use_multidb_server": True,
                "show_graph": True  # 顯示圖譜
            }
        }

        # 生成模型組合
        self.model_combinations = self._generate_model_combinations()

    def _generate_model_combinations(self) -> dict:
        """生成所有模型組合"""
        combinations = {}

        for llm_id, llm_info in self.llm_models.items():
            for rag_id, rag_info in self.rag_strategies.items():
                combo_id = f"{llm_id.replace(':', '-').replace('.', '-')}-{rag_id}"
                combinations[combo_id] = {
                    "model_id": llm_id,
                    "strategy_id": rag_id,
                    "display": f"{llm_info['display_name']} + {rag_info['display_name']}",
                    "backend_strategy": rag_info["backend_strategy"],
                    "use_multidb_server": rag_info.get("use_multidb_server", False),
                    "show_graph": rag_info.get("show_graph", False),
                    "performance_level": llm_info["performance"]
                }

        return combinations

    def query_neo4j_graph(self, entity_names: List[str], max_depth: int = 2) -> Dict[str, Any]:
        """
        查詢 Neo4j 獲取實體的關係圖譜

        Args:
            entity_names: 實體名稱列表(藝術家、藝術品等)
            max_depth: 關係深度

        Returns:
            包含節點和邊的圖譜數據
        """
        if not entity_names:
            return {"nodes": [], "edges": []}

        try:
            # 構建 Cypher 查詢 - 查找實體及其關係
            cypher_query = """
            MATCH (source)
            WHERE source.name IN $entity_names
               OR source.title IN $entity_names
            OPTIONAL MATCH path = (source)-[r*1..2]-(related)
            WITH source, relationships(path) as rels, nodes(path) as nodes_in_path
            UNWIND rels as rel
            WITH DISTINCT source, rel, startNode(rel) as start, endNode(rel) as end
            RETURN
                collect(DISTINCT {
                    id: id(source),
                    label: labels(source)[0],
                    name: coalesce(source.name, source.title, '未知'),
                    properties: properties(source)
                }) as source_nodes,
                collect(DISTINCT {
                    id: id(start),
                    label: labels(start)[0],
                    name: coalesce(start.name, start.title, '未知'),
                    properties: properties(start)
                }) +
                collect(DISTINCT {
                    id: id(end),
                    label: labels(end)[0],
                    name: coalesce(end.name, end.title, '未知'),
                    properties: properties(end)
                }) as all_nodes,
                collect(DISTINCT {
                    source: id(start),
                    target: id(end),
                    relationship: type(rel),
                    properties: properties(rel)
                }) as edges
            """

            response = requests.post(
                f"{self.neo4j_url}/db/neo4j/tx/commit",
                auth=self.neo4j_auth,
                json={
                    "statements": [{
                        "statement": cypher_query,
                        "parameters": {"entity_names": entity_names}
                    }]
                },
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("results") and result["results"][0].get("data"):
                    data = result["results"][0]["data"][0]["row"]

                    # 合併節點並去重
                    nodes_dict = {}
                    for node_list in [data[0], data[1]]:  # source_nodes + all_nodes
                        for node in node_list:
                            node_id = node.get("id")
                            if node_id and node_id not in nodes_dict:
                                nodes_dict[node_id] = node

                    return {
                        "nodes": list(nodes_dict.values()),
                        "edges": data[2],
                        "entity_count": len(nodes_dict),
                        "relationship_count": len(data[2])
                    }

            return {"nodes": [], "edges": [], "error": "查詢失敗"}

        except Exception as e:
            print(f"Neo4j graph query error: {str(e)}")
            return {"nodes": [], "edges": [], "error": str(e)}

    def extract_entities_from_context(self, contexts: List[Dict]) -> List[str]:
        """從檢索上下文中提取實體名稱"""
        entities = set()

        for ctx in contexts:
            metadata = ctx.get("metadata", {})
            # 提取藝術家名稱
            if "artist" in metadata:
                entities.add(metadata["artist"])
            if "name" in metadata:
                entities.add(metadata["name"])
            # 提取作品標題
            if "title" in metadata:
                entities.add(metadata["title"])
            # 從內容中提取(簡單方法,可以用NER改進)
            content = ctx.get("content", "")
            if isinstance(content, str) and len(content) > 0:
                # 這裡可以加入更複雜的實體識別邏輯
                pass

        return list(entities)[:10]  # 限制數量避免圖譜過大

    def format_graph_visualization(self, graph_data: Dict) -> str:
        """
        將圖譜數據格式化為可讀的文本表示
        OpenWebUI 支持 Markdown,我們用 Mermaid 圖表語法
        """
        if not graph_data.get("nodes"):
            return ""

        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])

        # 生成 Mermaid 流程圖
        mermaid_lines = ["```mermaid", "graph TD"]

        # 節點定義 (限制節點數量以保持可讀性)
        node_map = {}
        for i, node in enumerate(nodes[:20]):  # 最多20個節點
            node_id = f"N{i}"
            node_label = node.get("label", "Entity")
            node_name = node.get("name", "未知")[:20]  # 限制名稱長度

            # 根據類型設置不同樣式
            if node_label == "Artist":
                style = f"{node_id}[👨‍🎨 {node_name}]"
            elif node_label == "Artwork":
                style = f"{node_id}[🖼️ {node_name}]"
            elif node_label == "Style":
                style = f"{node_id}{{🎨 {node_name}}}"
            elif node_label == "Period":
                style = f"{node_id}{{📅 {node_name}}}"
            else:
                style = f"{node_id}[{node_name}]"

            mermaid_lines.append(f"    {style}")
            node_map[node.get("id")] = node_id

        # 邊定義
        for edge in edges[:30]:  # 最多30條邊
            source = node_map.get(edge.get("source"))
            target = node_map.get(edge.get("target"))
            rel_type = edge.get("relationship", "related")

            if source and target:
                # 關係類型的中文翻譯
                rel_translations = {
                    "CREATED": "創作",
                    "INFLUENCED": "影響",
                    "BELONGS_TO": "屬於",
                    "EXHIBITED_AT": "展出於",
                    "STUDIED_UNDER": "師從",
                    "CONTEMPORARY_OF": "同時代"
                }
                rel_label = rel_translations.get(rel_type, rel_type)
                mermaid_lines.append(f"    {source} -->|{rel_label}| {target}")

        mermaid_lines.append("```")

        # 添加圖例說明
        legend = f"""

### 📊 知識圖譜關係圖 ({graph_data.get('entity_count', 0)} 個實體, {graph_data.get('relationship_count', 0)} 個關係)

> 💡 **圖例說明:**
> - 👨‍🎨 方框 = 藝術家
> - 🖼️ 方框 = 藝術品
> - 🎨 菱形 = 藝術風格
> - 📅 菱形 = 時代/時期
> - 箭頭 = 實體間的關係

"""

        return legend + "\n".join(mermaid_lines)

    def is_service_available(self, url: str) -> bool:
        """檢查服務是否可用"""
        try:
            response = requests.get(f"{url}/health", timeout=2)
            return response.status_code == 200
        except:
            return False

    def get_best_available_server(self, use_multidb: bool = False, use_enhanced: bool = False) -> Optional[str]:
        """選擇最佳可用服務器"""
        if use_multidb and self.is_service_available(self.multidb_api_url):
            return self.multidb_api_url
        elif use_enhanced and self.is_service_available(self.enhanced_api_url):
            return self.enhanced_api_url
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

        # 默認使用 llama3.1:70b + Enhanced RAG
        return "llama3-1-70b-enhanced_rag"

    def query_rag_strategy(self, query: str, combo_id: str) -> dict:
        """查詢RAG策略服務器"""
        combo = self.model_combinations.get(combo_id)
        if not combo:
            return {"error": f"未知模型組合: {combo_id}"}

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
                    "show_graph": combo.get("show_graph", False)
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

def generate_comprehensive_answer(rag_result: dict, combo_info: dict) -> str:
    """生成包含圖譜視覺化的綜合回答"""

    answer_parts = []

    # 1. 主要答案
    main_answer = rag_result.get("answer", "無法生成回答")
    answer_parts.append(f"## 📝 回答\n\n{main_answer}\n")

    # 2. 知識圖譜視覺化 (如果啟用)
    if combo_info.get("show_graph", False) and rag_result.get("graph_data"):
        graph_viz = tools.format_graph_visualization(rag_result["graph_data"])
        if graph_viz:
            answer_parts.append(graph_viz)

    # 3. 檢索來源
    contexts = rag_result.get("contexts", [])
    if contexts:
        answer_parts.append("---\n\n### 📚 參考來源\n")
        for i, ctx in enumerate(contexts[:5], 1):
            score = ctx.get("score", "N/A")
            source = ctx.get("source_database", "unknown")
            method = ctx.get("retrieval_method", "unknown")

            content_preview = ctx.get("content", "")[:200]
            if len(ctx.get("content", "")) > 200:
                content_preview += "..."

            answer_parts.append(
                f"**{i}.** [{method}@{source}] (相關度: {score})\n"
                f"> {content_preview}\n"
            )

    # 4. 系統信息
    model_info = rag_result.get("model_combination", {})
    answer_parts.append(f"""
---

<details>
<summary>🔧 系統信息</summary>

- **LLM模型**: {model_info.get('llm_model', 'N/A')}
- **RAG策略**: {model_info.get('rag_strategy', 'N/A')}
- **數據源**: {model_info.get('primary_database', 'N/A')}
- **服務器**: {model_info.get('server_used', 'N/A')}
- **檢索項目**: {len(contexts)}

</details>
""")

    return "\n".join(answer_parts)

async def main(
    body: dict,
    __user__: dict = None,
    __event_emitter__ = None,
) -> str:
    """
    OpenWebUI主要入口函數 v6.0 - 帶圖譜視覺化
    """
    try:
        messages = body.get("messages", [])
        if not messages:
            return "👋 歡迎使用藝術史知識問答系統!"

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
            await __event_emitter__({
                "type": "status",
                "data": {"description": f"🚀 啟動 {combo_info['display']}...", "done": False}
            })

        # 檢查服務可用性
        server_url = tools.get_best_available_server(
            use_multidb=combo_info.get('use_multidb_server', False),
            use_enhanced=combo_info.get('use_enhanced_server', False)
        )
        if not server_url:
            return f"❌ RAG服務不可用。請確保服務器正在運行。\n\n嘗試的服務: {combo_info.get('display')}"

        # 執行檢索
        if __event_emitter__:
            await __event_emitter__({
                "type": "status",
                "data": {"description": f"🧠 執行檢索: {combo_info['backend_strategy']}...", "done": False}
            })

        rag_result = tools.query_rag_strategy(user_message, combo_id)

        if "error" in rag_result:
            return f"❌ 檢索錯誤: {rag_result['error']}"

        # 如果需要顯示圖譜,查詢 Neo4j
        if combo_info.get("show_graph", False):
            if __event_emitter__:
                await __event_emitter__({
                    "type": "status",
                    "data": {"description": "🕸️ 構建知識圖譜...", "done": False}
                })

            # 從上下文中提取實體
            contexts = rag_result.get("contexts", [])
            entities = tools.extract_entities_from_context(contexts)

            if entities:
                graph_data = tools.query_neo4j_graph(entities, max_depth=2)
                rag_result["graph_data"] = graph_data

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
        import traceback
        error_trace = traceback.format_exc()
        return f"❌ 系統錯誤: {str(e)}\n\n```\n{error_trace}\n```"
