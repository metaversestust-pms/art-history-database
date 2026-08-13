#!/usr/bin/env python3
"""
OpenWebUI模型註冊工具
用於批量註冊RAG+LLM組合模型到OpenWebUI
"""

import requests
import json
import time
from typing import Dict, List

class OpenWebUIModelRegistrator:
    def __init__(self, openwebui_url: str = "http://localhost:3000", api_key: str = None):
        """
        初始化OpenWebUI模型註冊器

        Args:
            openwebui_url: OpenWebUI服務URL
            api_key: API密鑰 (如果需要)
        """
        self.openwebui_url = openwebui_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()

        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})

    def get_model_combinations(self) -> List[Dict]:
        """獲取所有35種模型組合配置"""

        # LLM模型定義
        llm_models = {
            "gpt-oss:20b": {
                "display_name": "GPT-OSS 20B",
                "description": "開源GPT模型，20B參數，強大的語言理解能力",
                "icon": "🤖",
                "strengths": ["創意寫作", "複雜推理", "多語言支持"],
                "performance": "high"
            },
            "deepseek-r1:8b": {
                "display_name": "DeepSeek-R1 8B",
                "description": "專注推理的DeepSeek模型，8B參數",
                "icon": "🧠",
                "strengths": ["邏輯推理", "數學計算", "代碼生成"],
                "performance": "high"
            },
            "gemma3:1b": {
                "display_name": "Gemma3 1B",
                "description": "輕量級Gemma模型，1B參數，快速響應",
                "icon": "⚡",
                "strengths": ["快速響應", "資源效率", "基礎問答"],
                "performance": "fast"
            },
            "qwen3:4b": {
                "display_name": "Qwen3 4B",
                "description": "阿里巴巴Qwen模型，4B參數，中文優化",
                "icon": "🐲",
                "strengths": ["中文理解", "文化背景", "平衡性能"],
                "performance": "balanced"
            },
            "llama3.1:8b": {
                "display_name": "Llama 3.1 8B",
                "description": "Meta最新Llama模型，8B參數，全面優化",
                "icon": "🦙",
                "strengths": ["通用能力", "指令遵循", "安全性"],
                "performance": "balanced"
            }
        }

        # RAG策略定義
        rag_strategies = {
            "basic_rag": {
                "display_name": "基礎RAG",
                "description": "平衡的混合檢索策略，適合大多數查詢",
                "icon": "⚖️",
                "use_cases": ["通用問答", "基礎檢索", "平衡查詢"]
            },
            "advanced_rag": {
                "display_name": "Advanced RAG",
                "description": "多級檢索與重排序，提供深度分析",
                "icon": "🎯",
                "use_cases": ["複雜分析", "深度研究", "學術查詢"]
            },
            "vector_rag": {
                "display_name": "VectorRAG",
                "description": "純向量檢索，基於語義相似度",
                "icon": "🔍",
                "use_cases": ["相似內容", "語義搜索", "內容匹配"]
            },
            "graph_rag": {
                "display_name": "GraphRAG",
                "description": "知識圖譜檢索，探索概念關係",
                "icon": "🕸️",
                "use_cases": ["關係分析", "結構化查詢", "概念探索"]
            },
            "agentic_rag": {
                "display_name": "AgenticRAG",
                "description": "智能代理式推理，多步驟決策",
                "icon": "🤖",
                "use_cases": ["複雜推理", "多步分析", "智能決策"]
            },
            "self_rag": {
                "display_name": "SelfRAG",
                "description": "自我反思策略，迭代改進答案",
                "icon": "🔄",
                "use_cases": ["質量保證", "自我改進", "準確性驗證"]
            },
            "naive_rag": {
                "display_name": "NaiveRAG",
                "description": "最簡單的檢索策略，極速響應",
                "icon": "⚡",
                "use_cases": ["極速查詢", "簡單問答", "基礎匹配"]
            }
        }

        # 生成所有組合
        combinations = []
        for model_id, model_info in llm_models.items():
            for strategy_id, strategy_info in rag_strategies.items():
                combo_id = f"{model_id.replace(':', '-').replace('.', '-')}-{strategy_id}"

                combination = {
                    "id": combo_id,
                    "name": combo_id,
                    "display_name": f"{strategy_info['icon']} {model_info['display_name']} + {strategy_info['display_name']}",
                    "description": f"{model_info['description']} | {strategy_info['description']}",
                    "base_model": model_id,
                    "model_type": "chat",
                    "capabilities": ["chat", "vision"] if "gpt-oss" in model_id else ["chat"],
                    "tags": [
                        model_info['performance'],
                        "art-history",
                        "rag",
                        strategy_id.replace('_', '-')
                    ] + model_info['strengths'] + strategy_info['use_cases'],
                    "meta": {
                        "llm_model": model_id,
                        "llm_display": model_info['display_name'],
                        "rag_strategy": strategy_id,
                        "rag_display": strategy_info['display_name'],
                        "performance_level": model_info['performance'],
                        "strengths": model_info['strengths'],
                        "use_cases": strategy_info['use_cases'],
                        "icon": f"{model_info['icon']}{strategy_info['icon']}"
                    }
                }
                combinations.append(combination)

        return combinations

    def register_model(self, model_config: Dict) -> bool:
        """
        註冊單個模型到OpenWebUI

        Args:
            model_config: 模型配置

        Returns:
            bool: 註冊是否成功
        """
        try:
            # OpenWebUI模型註冊API端點 (可能需要根據實際API調整)
            url = f"{self.openwebui_url}/api/models"

            # 構建註冊數據
            model_data = {
                "id": model_config["id"],
                "name": model_config["name"],
                "meta": {
                    "description": model_config["description"],
                    "capabilities": model_config["capabilities"],
                    "tags": model_config["tags"],
                    **model_config["meta"]
                }
            }

            response = self.session.post(url, json=model_data)

            if response.status_code in [200, 201]:
                print(f"✅ 成功註冊模型: {model_config['display_name']}")
                return True
            else:
                print(f"❌ 註冊失敗: {model_config['display_name']} - {response.status_code}: {response.text}")
                return False

        except Exception as e:
            print(f"❌ 註冊異常: {model_config['display_name']} - {str(e)}")
            return False

    def register_priority_models(self) -> Dict:
        """註冊高優先級模型組合"""

        priority_models = [
            "qwen3-4b-basic_rag",      # 中文場景最佳平衡
            "gpt-oss-20b-agentic_rag", # 最強智能分析
            "gemma3-1b-naive_rag",     # 極速響應
            "deepseek-r1-8b-self_rag", # 高準確推理
            "llama3-1-8b-graph_rag",   # 關係分析
            "qwen3-4b-vector_rag",     # 中文語義搜索
            "gpt-oss-20b-advanced_rag",# 深度分析
            "gemma3-1b-basic_rag",     # 快速通用
        ]

        all_combinations = self.get_model_combinations()
        priority_combinations = [
            combo for combo in all_combinations
            if combo["id"] in priority_models
        ]

        results = {"success": 0, "failed": 0, "details": []}

        print(f"🚀 開始註冊 {len(priority_combinations)} 個優先級模型...")

        for combo in priority_combinations:
            success = self.register_model(combo)
            if success:
                results["success"] += 1
            else:
                results["failed"] += 1

            results["details"].append({
                "model": combo["id"],
                "display": combo["display_name"],
                "success": success
            })

            # 避免API限流
            time.sleep(1)

        return results

    def register_all_models(self) -> Dict:
        """註冊所有35種模型組合"""

        all_combinations = self.get_model_combinations()
        results = {"success": 0, "failed": 0, "details": []}

        print(f"🚀 開始註冊全部 {len(all_combinations)} 個模型組合...")

        for i, combo in enumerate(all_combinations, 1):
            print(f"\n📝 [{i}/{len(all_combinations)}] 註冊: {combo['display_name']}")

            success = self.register_model(combo)
            if success:
                results["success"] += 1
            else:
                results["failed"] += 1

            results["details"].append({
                "model": combo["id"],
                "display": combo["display_name"],
                "success": success
            })

            # 避免API限流
            time.sleep(2)

        return results

    def generate_modelfile(self, combo_id: str) -> str:
        """為組合生成Ollama Modelfile"""

        all_combinations = self.get_model_combinations()
        combo = next((c for c in all_combinations if c["id"] == combo_id), None)

        if not combo:
            return f"# 錯誤: 未找到組合 {combo_id}"

        modelfile = f"""# Modelfile for {combo['display_name']}
# 藝術史RAG+LLM組合模型

FROM {combo['base_model']}

# 模型參數
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER repeat_penalty 1.1

# 系統提示
SYSTEM \"\"\"你是一個專業的藝術史智能助手，使用 {combo['meta']['rag_display']} 策略進行知識檢索和回答。

模型特色：{combo['description']}

優勢能力：{', '.join(combo['meta']['strengths'])}
適用場景：{', '.join(combo['meta']['use_cases'])}

請基於檢索到的藝術史知識，提供準確、詳細且富有洞察力的回答。
\"\"\"

# 模型標籤
LABEL "art-history" "true"
LABEL "rag-strategy" "{combo['meta']['rag_strategy']}"
LABEL "llm-model" "{combo['meta']['llm_model']}"
LABEL "performance" "{combo['meta']['performance_level']}"
"""
        return modelfile

    def export_all_modelfiles(self, output_dir: str = "./modelfiles") -> None:
        """導出所有組合的Modelfile"""

        import os
        os.makedirs(output_dir, exist_ok=True)

        all_combinations = self.get_model_combinations()

        print(f"📁 導出Modelfile到: {output_dir}")

        for combo in all_combinations:
            modelfile_content = self.generate_modelfile(combo["id"])
            file_path = os.path.join(output_dir, f"{combo['id']}.Modelfile")

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modelfile_content)

            print(f"✅ {combo['id']}.Modelfile")

        print(f"\n🎉 完成！導出了 {len(all_combinations)} 個Modelfile")

def main():
    """主程序"""
    print("🎨 藝術史RAG+LLM組合模型註冊工具")
    print("=" * 50)

    # 初始化註冊器
    registrator = OpenWebUIModelRegistrator()

    while True:
        print("\n請選擇操作:")
        print("1. 註冊優先級模型 (8個)")
        print("2. 註冊所有模型 (35個)")
        print("3. 生成單個Modelfile")
        print("4. 導出所有Modelfile")
        print("5. 查看模型組合清單")
        print("0. 退出")

        choice = input("\n輸入選項 (0-5): ").strip()

        if choice == "1":
            print("\n🚀 註冊優先級模型...")
            results = registrator.register_priority_models()
            print(f"\n📊 註冊結果: 成功 {results['success']} 個，失敗 {results['failed']} 個")

        elif choice == "2":
            confirm = input("\n⚠️  這將註冊全部35個模型，確定嗎？(y/N): ").strip().lower()
            if confirm == 'y':
                results = registrator.register_all_models()
                print(f"\n📊 註冊結果: 成功 {results['success']} 個，失敗 {results['failed']} 個")

        elif choice == "3":
            combo_id = input("\n輸入組合ID (例: qwen3-4b-basic_rag): ").strip()
            modelfile = registrator.generate_modelfile(combo_id)
            print(f"\n📄 Modelfile for {combo_id}:")
            print("-" * 40)
            print(modelfile)

        elif choice == "4":
            output_dir = input("\n輸入輸出目錄 (預設: ./modelfiles): ").strip()
            if not output_dir:
                output_dir = "./modelfiles"
            registrator.export_all_modelfiles(output_dir)

        elif choice == "5":
            combinations = registrator.get_model_combinations()
            print(f"\n📋 所有 {len(combinations)} 種模型組合:")
            print("-" * 60)
            for i, combo in enumerate(combinations, 1):
                print(f"{i:2d}. {combo['id']}")
                print(f"    {combo['display_name']}")
                print(f"    {combo['description'][:80]}...")
                print()

        elif choice == "0":
            print("👋 再見！")
            break

        else:
            print("❌ 無效選項，請重新選擇")

if __name__ == "__main__":
    main()