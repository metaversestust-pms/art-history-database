#!/usr/bin/env python3
"""
更新 RAG 配置腳本
新增 gpt-oss:20b 模型和 naive_rag 策略
並為指定的 5 個 LLM 模型生成所有 RAG 策略組合
"""

import json
from pathlib import Path

# 指定的 LLM 模型
REQUIRED_MODELS = [
    "llama3.1:8b",
    "deepseek-r1:8b",
    "gemma3:4b",
    "qwen3:8b",
    "gpt-oss:20b"  # 新增
]

# 指定的 RAG 策略
REQUIRED_STRATEGIES = [
    "vector_only",    # VectorRAG
    "graph_only",     # GraphRAG
    "advanced_rag",   # Advanced RAG
    "agentic_rag",    # AgenticRAG
    "self_rag",       # SelfRAG
    "naive_rag"       # Naive RAG (新增)
]

def load_config():
    """載入現有配置"""
    config_path = Path("langchain-rag/rag_config.json")
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_config(config):
    """保存配置"""
    config_path = Path("langchain-rag/rag_config.json")
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def add_gpt_oss_model(config):
    """新增 gpt-oss:20b 模型"""
    if "gpt-oss:20b" not in config["llm_models"]:
        config["llm_models"]["gpt-oss:20b"] = {
            "name": "GPT-OSS 20B",
            "display_name": "🤖 GPT-OSS 20B",
            "provider": "ollama",
            "context_length": 131072,
            "temperature_default": 0.1,
            "description": "開源GPT模型，20B參數，強大的語言理解能力"
        }
        print("✅ 新增 gpt-oss:20b 模型")
    else:
        print("ℹ️  gpt-oss:20b 模型已存在")

def add_naive_rag_strategy(config):
    """新增 naive_rag 策略"""
    if "naive_rag" not in config["rag_strategies"]:
        config["rag_strategies"]["naive_rag"] = {
            "name": "Naive RAG",
            "display_name": "📝 Naive RAG",
            "emoji": "📝",
            "description": "基礎檢索生成"
        }
        print("✅ 新增 naive_rag 策略")
    else:
        print("ℹ️  naive_rag 策略已存在")

def generate_model_combinations(config):
    """為指定的模型和策略生成所有組合"""

    # 清除現有組合，只保留我們需要的
    new_combinations = []

    for model_id in REQUIRED_MODELS:
        if model_id not in config["llm_models"]:
            print(f"⚠️  模型 {model_id} 不存在於配置中，跳過")
            continue

        model_info = config["llm_models"][model_id]

        for strategy_id in REQUIRED_STRATEGIES:
            if strategy_id not in config["rag_strategies"]:
                print(f"⚠️  策略 {strategy_id} 不存在於配置中，跳過")
                continue

            strategy_info = config["rag_strategies"][strategy_id]

            combination_id = f"{model_id}@{strategy_id}"

            combination = {
                "id": combination_id,
                "name": f"{model_info['display_name']} + {strategy_info['display_name']}",
                "display_name": f"{strategy_info['emoji']} {model_info['name']} + {strategy_info['name']}",
                "description": f"{model_info['description']} + {strategy_info['description']}",
                "llm_model": model_id,
                "rag_strategy": strategy_id,
                "enabled": True,
                "meta": {
                    "llm": model_info,
                    "rag": strategy_info
                },
                "params": {
                    "temperature": model_info["temperature_default"],
                    "max_tokens": 2048,
                    "use_rag": True
                }
            }

            new_combinations.append(combination)

    return new_combinations

def main():
    """主函數"""
    print("=" * 60)
    print("更新 RAG 配置")
    print("=" * 60)

    # 載入配置
    print("\n📂 載入現有配置...")
    config = load_config()

    # 新增 gpt-oss:20b 模型
    print("\n🔧 新增 gpt-oss:20b 模型...")
    add_gpt_oss_model(config)

    # 新增 naive_rag 策略
    print("\n🔧 新增 naive_rag 策略...")
    add_naive_rag_strategy(config)

    # 生成新的組合
    print("\n🔄 生成模型組合...")
    new_combinations = generate_model_combinations(config)
    config["model_combinations"] = new_combinations

    # 保存配置
    print(f"\n💾 保存配置... ({len(new_combinations)} 個組合)")
    save_config(config)

    # 總結
    print("\n" + "=" * 60)
    print("✅ 配置更新完成!")
    print(f"   - LLM 模型數量: {len(REQUIRED_MODELS)}")
    print(f"   - RAG 策略數量: {len(REQUIRED_STRATEGIES)}")
    print(f"   - 總組合數量: {len(new_combinations)}")
    print("=" * 60)

    # 列出所有組合
    print("\n📋 生成的組合清單:")
    print("-" * 60)
    for i, combo in enumerate(new_combinations, 1):
        print(f"{i:2d}. {combo['display_name']}")
    print("-" * 60)

if __name__ == "__main__":
    main()
