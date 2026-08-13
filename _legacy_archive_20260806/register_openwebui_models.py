#!/usr/bin/env python3
"""
OpenWebUI模型註冊工具
自動註冊5種LLM模型 × 6種RAG策略 = 30種組合到OpenWebUI
"""

import json
import subprocess
import os
import time
from typing import Dict, List, Any

class OpenWebUIModelRegistrar:
    def __init__(self):
        self.llm_models = {
            "gpt-oss:20b": {
                "display_name": "GPT-OSS 20B",
                "description": "開源GPT模型，20B參數，強大的語言理解能力",
                "base_model": "gpt-oss:20b"
            },
            "deepseek-r1:8b": {
                "display_name": "DeepSeek-R1 8B",
                "description": "專注推理的DeepSeek模型，8B參數",
                "base_model": "deepseek-r1:8b"
            },
            "gemma3:1b": {
                "display_name": "Gemma3 1B",
                "description": "輕量級Gemma模型，1B參數，快速響應",
                "base_model": "gemma3:1b"
            },
            "qwen3:4b": {
                "display_name": "Qwen3 4B",
                "description": "阿里巴巴Qwen模型，4B參數，中文優化",
                "base_model": "qwen3:4b"
            },
            "llama3.1:8b": {
                "display_name": "Llama 3.1 8B",
                "description": "Meta最新Llama模型，8B參數，全面優化",
                "base_model": "llama3.1:8b"
            }
        }

        self.rag_strategies = {
            "basic_rag": {
                "display_name": "基礎RAG",
                "description": "平衡的混合檢索策略，適合大多數查詢",
                "icon": "⚖️"
            },
            "advanced_rag": {
                "display_name": "Advanced RAG",
                "description": "多級檢索與重排序，提供深度分析",
                "icon": "🎯"
            },
            "vector_rag": {
                "display_name": "VectorRAG",
                "description": "純向量檢索，基於語義相似度",
                "icon": "🔍"
            },
            "graph_rag": {
                "display_name": "GraphRAG",
                "description": "知識圖譜檢索，探索概念關係",
                "icon": "🕸️"
            },
            "agentic_rag": {
                "display_name": "AgenticRAG",
                "description": "智能代理式推理，多步驟決策",
                "icon": "🤖"
            },
            "self_rag": {
                "display_name": "SelfRAG",
                "description": "自我反思策略，迭代改進答案",
                "icon": "🔄"
            }
        }

    def generate_modelfile(self, model_id: str, strategy_id: str) -> str:
        """生成Ollama Modelfile內容"""
        model_info = self.llm_models[model_id]
        strategy_info = self.rag_strategies[strategy_id]

        combo_name = f"{model_id.replace(':', '-')}-{strategy_id}"

        modelfile_content = f'''FROM {model_info["base_model"]}

# 藝術史RAG+LLM組合模型
# LLM: {model_info["display_name"]}
# RAG: {strategy_info["icon"]} {strategy_info["display_name"]}

TEMPLATE """{{{{ if .System }}}}System: {{{{ .System }}}}

{{{{ end }}}}User: {{{{ .Prompt }}}}