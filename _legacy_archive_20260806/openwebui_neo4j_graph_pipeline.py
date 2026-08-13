"""
title: Neo4j 知識圖譜視覺化管道
author: Art History Database Team
version: 1.0.0
description: 為所有 RAG 組合模型添加 Neo4j 知識圖譜視覺化功能
required_open_webui_version: 0.3.0
"""

from typing import List, Optional, Dict, Any, Iterator
from pydantic import BaseModel, Field
import requests
import json
import re
import os


class Pipeline:
    """
    OpenWebUI Pipeline: 攔截 Ollama RAG 模型響應並添加圖譜視覺化

    工作原理:
    1. 用戶提問 → Ollama RAG 模型生成回答
    2. Pipeline 攔截回答和用戶問題
    3. 從問題和回答中提取實體
    4. 查詢 Neo4j 獲取關係圖譜
    5. 生成 Mermaid 圖表
    6. 將圖譜添加到原始回答中
    """

    class Valves(BaseModel):
        """管道配置參數"""
        NEO4J_URI: str = Field(
            default="http://localhost:7474",
            description="Neo4j HTTP API 地址"
        )
        NEO4J_USER: str = Field(
            default="neo4j",
            description="Neo4j 用戶名"
        )
        NEO4J_PASSWORD: str = Field(
            default="arthistory123",
            description="Neo4j 密碼"
        )
        ENABLE_GRAPH_VIZ: bool = Field(
            default=True,
            description="啟用圖譜視覺化"
        )
        MAX_GRAPH_NODES: int = Field(
            default=15,
            description="最大圖譜節點數量"
        )
        MAX_GRAPH_DEPTH: int = Field(
            default=2,
            description="圖譜查詢深度 (1-3)"
        )
        SUPPORTED_RAG_MODELS: str = Field(
            default="graph-rag,hybrid-rag,advanced-rag,agentic-rag",
            description="支持圖譜的 RAG 模型關鍵字(逗號分隔)"
        )

    def __init__(self):
        self.type = "filter"
        self.name = "Neo4j Graph Visualization"
        self.valves = self.Valves()

    def is_graph_enabled_model(self, model_id: str) -> bool:
        """檢查模型是否支持圖譜視覺化"""
        if not self.valves.ENABLE_GRAPH_VIZ:
            return False

        supported_keywords = [
            kw.strip()
            for kw in self.valves.SUPPORTED_RAG_MODELS.split(",")
        ]

        model_lower = model_id.lower()
        return any(keyword in model_lower for keyword in supported_keywords)

    def extract_entities_from_text(self, text: str) -> List[str]:
        """
        從文本中提取實體名稱

        簡單方法: 提取中文大寫字母開頭的詞組和專有名詞
        可以改進為使用 NER 模型
        """
        entities = set()

        # 提取常見藝術家名稱 (中文和英文)
        artist_patterns = [
            r'(達文西|米開朗基羅|拉斐爾|提香|卡拉瓦喬)',
            r'(Leonardo da Vinci|Michelangelo|Raphael|Titian|Caravaggio)',
            r'(莫內|梵谷|畢卡索|塞尚|雷諾瓦)',
            r'(Monet|Van Gogh|Picasso|Cézanne|Renoir)',
        ]

        for pattern in artist_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities.update(matches)

        # 提取作品名稱 (帶引號或書名號)
        artwork_patterns = [
            r'[《「『]([^》」』]+)[》」』]',  # 中文引號
            r'"([^"]+)"',  # 英文引號
            r"'([^']+)'",
        ]

        for pattern in artwork_patterns:
            matches = re.findall(pattern, text)
            entities.update([m for m in matches if len(m) > 2])

        # 提取大寫開頭的專有名詞 (英文)
        proper_nouns = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', text)
        entities.update([n for n in proper_nouns if len(n) > 3])

        return list(entities)[:10]  # 限制數量

    def query_neo4j_graph(
        self,
        entity_names: List[str],
        max_depth: int = 2
    ) -> Dict[str, Any]:
        """查詢 Neo4j 獲取實體關係圖譜"""

        if not entity_names:
            return {"nodes": [], "edges": []}

        try:
            # 構建 Cypher 查詢
            cypher_query = """
            MATCH (source)
            WHERE source.name IN $entity_names
               OR source.title IN $entity_names
            OPTIONAL MATCH path = (source)-[r*1..2]-(related)
            WITH source, relationships(path) as rels
            UNWIND rels as rel
            WITH DISTINCT source, rel, startNode(rel) as start, endNode(rel) as end
            RETURN
                collect(DISTINCT {
                    id: id(source),
                    label: labels(source)[0],
                    name: coalesce(source.name, source.title, '未知')
                }) as source_nodes,
                collect(DISTINCT {
                    id: id(start),
                    label: labels(start)[0],
                    name: coalesce(start.name, start.title, '未知')
                }) +
                collect(DISTINCT {
                    id: id(end),
                    label: labels(end)[0],
                    name: coalesce(end.name, end.title, '未知')
                }) as all_nodes,
                collect(DISTINCT {
                    source: id(start),
                    target: id(end),
                    relationship: type(rel)
                }) as edges
            """

            response = requests.post(
                f"{self.valves.NEO4J_URI}/db/neo4j/tx/commit",
                auth=(self.valves.NEO4J_USER, self.valves.NEO4J_PASSWORD),
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

                    # 合併並去重節點
                    nodes_dict = {}
                    for node_list in [data[0], data[1]]:
                        for node in node_list:
                            node_id = node.get("id")
                            if node_id and node_id not in nodes_dict:
                                nodes_dict[node_id] = node

                    return {
                        "nodes": list(nodes_dict.values())[:self.valves.MAX_GRAPH_NODES],
                        "edges": data[2][:30],  # 限制關係數量
                        "entity_count": len(nodes_dict),
                        "relationship_count": len(data[2])
                    }

            return {"nodes": [], "edges": []}

        except Exception as e:
            print(f"[Neo4j Graph Pipeline] Query error: {str(e)}")
            return {"nodes": [], "edges": [], "error": str(e)}

    def format_mermaid_graph(self, graph_data: Dict) -> str:
        """生成 Mermaid 圖表"""

        if not graph_data.get("nodes"):
            return ""

        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])

        mermaid_lines = ["```mermaid", "graph TD"]

        # 節點定義
        node_map = {}
        for i, node in enumerate(nodes):
            node_id = f"N{i}"
            node_label = node.get("label", "Entity")
            node_name = node.get("name", "未知")[:20]

            # 根據類型設置樣式
            if node_label == "Artist":
                style = f"{node_id}[👨‍🎨 {node_name}]"
            elif node_label == "Artwork":
                style = f"{node_id}[🖼️ {node_name}]"
            elif node_label == "Style":
                style = f"{node_id}{{{node_name}}}"
            elif node_label == "Period":
                style = f"{node_id}{{{node_name}}}"
            elif node_label == "Museum":
                style = f"{node_id}[🏛️ {node_name}]"
            else:
                style = f"{node_id}[{node_name}]"

            mermaid_lines.append(f"    {style}")
            node_map[node.get("id")] = node_id

        # 邊定義
        rel_translations = {
            "CREATED": "創作",
            "INFLUENCED": "影響",
            "BELONGS_TO": "屬於",
            "EXHIBITED_AT": "展出於",
            "STUDIED_UNDER": "師從",
            "CONTEMPORARY_OF": "同時代",
            "LOCATED_IN": "位於",
            "PART_OF": "屬於時期"
        }

        for edge in edges:
            source = node_map.get(edge.get("source"))
            target = node_map.get(edge.get("target"))
            rel_type = edge.get("relationship", "related")

            if source and target:
                rel_label = rel_translations.get(rel_type, rel_type)
                mermaid_lines.append(f"    {source} -->|{rel_label}| {target}")

        mermaid_lines.append("```")

        # 添加圖例
        legend = f"""

### 📊 知識圖譜關係圖

> **找到 {graph_data.get('entity_count', 0)} 個實體, {graph_data.get('relationship_count', 0)} 個關係**

> 💡 **圖例**: 👨‍🎨 藝術家 | 🖼️ 作品 | 🎨 風格 | 📅 時期 | 🏛️ 博物館

"""

        return legend + "\n".join(mermaid_lines)

    def pipe(
        self,
        user_message: str,
        model_id: str,
        messages: List[dict],
        body: dict
    ) -> str:
        """
        Pipeline 主要方法: 在 Ollama 模型生成回答後處理

        Args:
            user_message: 用戶最新的消息
            model_id: 使用的模型 ID
            messages: 對話歷史
            body: 請求體

        Returns:
            增強後的響應文本
        """

        # 檢查是否需要添加圖譜
        if not self.is_graph_enabled_model(model_id):
            return None  # 不處理,讓原始響應通過

        print(f"[Neo4j Graph Pipeline] Processing model: {model_id}")

        # Ollama 已經生成了回答,我們需要在 outlet 中處理
        # 這裡返回 None 表示不修改請求,在 outlet 中處理響應
        return None

    async def outlet(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __event_emitter__=None,
        __event_call__=None
    ) -> dict:
        """
        處理 Ollama 模型的響應並添加圖譜

        這個方法在模型生成回答後被調用
        """

        model_id = body.get("model", "")

        # 檢查是否需要處理
        if not self.is_graph_enabled_model(model_id):
            return body

        # 獲取用戶消息
        messages = body.get("messages", [])
        if not messages:
            return body

        # 提取最新用戶消息
        user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break

        if not user_message:
            return body

        # 發送狀態更新
        if __event_emitter__:
            await __event_emitter__({
                "type": "status",
                "data": {
                    "description": "🕸️ 構建知識圖譜...",
                    "done": False
                }
            })

        # 提取實體
        entities = self.extract_entities_from_text(user_message)

        print(f"[Neo4j Graph Pipeline] Extracted entities: {entities}")

        if not entities:
            # 嘗試從助手的最後回答中提取
            for msg in reversed(messages):
                if msg.get("role") == "assistant":
                    assistant_message = msg.get("content", "")
                    entities = self.extract_entities_from_text(assistant_message)
                    if entities:
                        break

        if not entities:
            print("[Neo4j Graph Pipeline] No entities found")
            return body

        # 查詢圖譜
        graph_data = self.query_neo4j_graph(
            entities,
            max_depth=self.valves.MAX_GRAPH_DEPTH
        )

        if graph_data.get("nodes"):
            # 生成 Mermaid 圖表
            mermaid_viz = self.format_mermaid_graph(graph_data)

            # 將圖表添加到最後一條助手消息
            for msg in reversed(messages):
                if msg.get("role") == "assistant":
                    original_content = msg.get("content", "")

                    # 在原始回答後添加圖譜
                    enhanced_content = f"{original_content}\n\n---\n{mermaid_viz}"
                    msg["content"] = enhanced_content

                    print(f"[Neo4j Graph Pipeline] Added graph with {len(graph_data['nodes'])} nodes")
                    break

            if __event_emitter__:
                await __event_emitter__({
                    "type": "status",
                    "data": {
                        "description": f"✅ 圖譜已添加 ({len(graph_data['nodes'])} 個節點)",
                        "done": True
                    }
                })

        return body
