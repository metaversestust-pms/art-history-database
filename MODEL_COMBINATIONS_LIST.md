# 🎨 藝術史RAG+LLM模型組合完整清單

## 📊 系統概述

**總組合數量**: 35種 (5個LLM模型 × 7種RAG策略)

**服務端點**:
- RAG管理API: `http://localhost:8008`
- OpenWebUI整合: `http://localhost:8009`

## 🤖 支援的LLM模型 (5種)

| 模型ID | 顯示名稱 | 參數大小 | 特色 | 適用場景 |
|--------|----------|----------|------|----------|
| `gpt-oss:20b` | GPT-OSS 20B | 20B | 強大語言理解、創意寫作 | 複雜推理、多語言支持 |
| `deepseek-r1:8b` | DeepSeek-R1 8B | 8B | 專注推理、邏輯分析 | 數學計算、代碼生成 |
| `gemma3:1b` | Gemma3 1B | 1B | 輕量級、極速響應 | 快速問答、資源受限環境 |
| `qwen3:4b` | Qwen3 4B | 4B | 中文優化、平衡性能 | 中文理解、文化背景 |
| `llama3.1:8b` | Llama 3.1 8B | 8B | 通用能力、指令遵循 | 通用場景、安全性要求 |

## 🔍 支援的RAG策略 (7種)

| 策略ID | 圖標 | 顯示名稱 | 後端策略 | 描述 | 適用場景 |
|--------|------|----------|----------|------|----------|
| `basic_rag` | ⚖️ | 基礎RAG | hybrid_balanced | 平衡混合策略 | 通用問答、基礎檢索 |
| `advanced_rag` | 🎯 | Advanced RAG | advanced_rag | 多級檢索與重排序 | 複雜分析、深度研究 |
| `vector_rag` | 🔍 | VectorRAG | vector_only | 純向量語義檢索 | 相似內容、語義搜索 |
| `graph_rag` | 🕸️ | GraphRAG | graph_only | 知識圖譜關係檢索 | 關係分析、結構化查詢 |
| `agentic_rag` | 🤖 | AgenticRAG | agentic_rag | 智能代理式推理 | 複雜推理、多步分析 |
| `self_rag` | 🔄 | SelfRAG | self_rag | 自我反思迭代改進 | 質量保證、準確性驗證 |
| `naive_rag` | ⚡ | NaiveRAG | naive_rag | 最簡單策略，極速響應 | 極速查詢、簡單問答 |

## 📋 完整組合清單 (35種)

### GPT-OSS 20B 組合 (7種)
1. `gpt-oss-20b-basic_rag` - 🤖 GPT-OSS 20B + ⚖️ 基礎RAG
2. `gpt-oss-20b-advanced_rag` - 🤖 GPT-OSS 20B + 🎯 Advanced RAG
3. `gpt-oss-20b-vector_rag` - 🤖 GPT-OSS 20B + 🔍 VectorRAG
4. `gpt-oss-20b-graph_rag` - 🤖 GPT-OSS 20B + 🕸️ GraphRAG
5. `gpt-oss-20b-agentic_rag` - 🤖 GPT-OSS 20B + 🤖 AgenticRAG
6. `gpt-oss-20b-self_rag` - 🤖 GPT-OSS 20B + 🔄 SelfRAG
7. `gpt-oss-20b-naive_rag` - 🤖 GPT-OSS 20B + ⚡ NaiveRAG

### DeepSeek-R1 8B 組合 (7種)
8. `deepseek-r1-8b-basic_rag` - 🧠 DeepSeek-R1 8B + ⚖️ 基礎RAG
9. `deepseek-r1-8b-advanced_rag` - 🧠 DeepSeek-R1 8B + 🎯 Advanced RAG
10. `deepseek-r1-8b-vector_rag` - 🧠 DeepSeek-R1 8B + 🔍 VectorRAG
11. `deepseek-r1-8b-graph_rag` - 🧠 DeepSeek-R1 8B + 🕸️ GraphRAG
12. `deepseek-r1-8b-agentic_rag` - 🧠 DeepSeek-R1 8B + 🤖 AgenticRAG
13. `deepseek-r1-8b-self_rag` - 🧠 DeepSeek-R1 8B + 🔄 SelfRAG
14. `deepseek-r1-8b-naive_rag` - 🧠 DeepSeek-R1 8B + ⚡ NaiveRAG

### Gemma3 1B 組合 (7種)
15. `gemma3-1b-basic_rag` - ⚡ Gemma3 1B + ⚖️ 基礎RAG
16. `gemma3-1b-advanced_rag` - ⚡ Gemma3 1B + 🎯 Advanced RAG
17. `gemma3-1b-vector_rag` - ⚡ Gemma3 1B + 🔍 VectorRAG
18. `gemma3-1b-graph_rag` - ⚡ Gemma3 1B + 🕸️ GraphRAG
19. `gemma3-1b-agentic_rag` - ⚡ Gemma3 1B + 🤖 AgenticRAG
20. `gemma3-1b-self_rag` - ⚡ Gemma3 1B + 🔄 SelfRAG
21. `gemma3-1b-naive_rag` - ⚡ Gemma3 1B + ⚡ NaiveRAG

### Qwen3 4B 組合 (7種)
22. `qwen3-4b-basic_rag` - 🐲 Qwen3 4B + ⚖️ 基礎RAG
23. `qwen3-4b-advanced_rag` - 🐲 Qwen3 4B + 🎯 Advanced RAG
24. `qwen3-4b-vector_rag` - 🐲 Qwen3 4B + 🔍 VectorRAG
25. `qwen3-4b-graph_rag` - 🐲 Qwen3 4B + 🕸️ GraphRAG
26. `qwen3-4b-agentic_rag` - 🐲 Qwen3 4B + 🤖 AgenticRAG
27. `qwen3-4b-self_rag` - 🐲 Qwen3 4B + 🔄 SelfRAG
28. `qwen3-4b-naive_rag` - 🐲 Qwen3 4B + ⚡ NaiveRAG

### Llama 3.1 8B 組合 (7種)
29. `llama3-1-8b-basic_rag` - 🦙 Llama 3.1 8B + ⚖️ 基礎RAG
30. `llama3-1-8b-advanced_rag` - 🦙 Llama 3.1 8B + 🎯 Advanced RAG
31. `llama3-1-8b-vector_rag` - 🦙 Llama 3.1 8B + 🔍 VectorRAG
32. `llama3-1-8b-graph_rag` - 🦙 Llama 3.1 8B + 🕸️ GraphRAG
33. `llama3-1-8b-agentic_rag` - 🦙 Llama 3.1 8B + 🤖 AgenticRAG
34. `llama3-1-8b-self_rag` - 🦙 Llama 3.1 8B + 🔄 SelfRAG
35. `llama3-1-8b-naive_rag` - 🦙 Llama 3.1 8B + ⚡ NaiveRAG

## 🎯 推薦組合

### 按使用場景分類

#### 🚀 極速響應 (< 0.1秒)
- `gemma3-1b-naive_rag` - 最快的組合，適合簡單查詢
- `qwen3-4b-naive_rag` - 中文優化的快速響應

#### ⚖️ 平衡性能 (0.1-0.5秒)
- `qwen3-4b-basic_rag` - 中文場景的最佳平衡
- `llama3-1-8b-basic_rag` - 通用場景推薦
- `deepseek-r1-8b-vector_rag` - 語義搜索優化

#### 🎯 高質量分析 (0.5-1.0秒)
- `gpt-oss-20b-advanced_rag` - 最全面的分析能力
- `deepseek-r1-8b-self_rag` - 高準確性推理
- `llama3-1-8b-agentic_rag` - 智能代理分析

#### 🕸️ 關係探索 (0.2-0.8秒)
- `gpt-oss-20b-graph_rag` - 深度關係分析
- `deepseek-r1-8b-graph_rag` - 邏輯關係推理
- `qwen3-4b-graph_rag` - 中文文化關係

### 按查詢類型分類

#### 📚 事實性問答
- **首選**: `qwen3-4b-vector_rag`
- **備選**: `llama3-1-8b-basic_rag`

#### 🧮 複雜推理分析
- **首選**: `gpt-oss-20b-agentic_rag`
- **備選**: `deepseek-r1-8b-self_rag`

#### 🔗 關係性查詢
- **首選**: `gpt-oss-20b-graph_rag`
- **備選**: `deepseek-r1-8b-graph_rag`

#### ⚡ 簡單快速查詢
- **首選**: `gemma3-1b-naive_rag`
- **備選**: `qwen3-4b-naive_rag`

## 📊 性能指標

| 性能級別 | 模型組合示例 | 預期響應時間 | 適用場景 |
|----------|-------------|--------------|----------|
| **極速** | gemma3-1b + naive_rag | < 0.1秒 | 簡單問答 |
| **快速** | qwen3-4b + vector_rag | 0.1-0.3秒 | 語義搜索 |
| **平衡** | llama3-1-8b + basic_rag | 0.3-0.5秒 | 通用查詢 |
| **高質量** | gpt-oss-20b + advanced_rag | 0.5-1.0秒 | 深度分析 |
| **專業級** | gpt-oss-20b + agentic_rag | 0.8-1.5秒 | 專業研究 |

## 🔧 部署注意事項

### OpenWebUI 模型配置
每個組合都需要在 OpenWebUI 中註冊為獨立的模型，模型名稱格式：
```
{llm-model-id}-{rag-strategy-id}
```

### 環境變數配置
```bash
# 非Docker環境
export DOCKER_ENV=false

# Docker環境
export DOCKER_ENV=true
```

### 服務依賴
1. **RAG管理API** (端口8008) - 必須先啟動
2. **Neo4j資料庫** - 支援GraphRAG策略
3. **向量資料庫** - 支援VectorRAG策略
4. **OpenWebUI** - 最終用戶界面

---

**📅 最後更新**: 2025-09-28
**🔖 版本**: v3.0
**👥 維護團隊**: Art History Database Team