# 🎉 完整的LLM+RAG組合模型列表

**創建時間**: 2025-10-20
**總計**: 35個RAG組合模型 + 7個基礎LLM = 42個模型

---

## 📊 模型統計

### RAG組合模型 (35個)
- **Llama 3.1:8b 系列**: 7個
- **Qwen3:4b 系列**: 7個
- **Qwen3:8b 系列**: 7個
- **DeepSeek-R1:8b 系列**: 7個
- **Gemma3:4b 系列**: 7個

### 基礎LLM模型 (7個)
- llama3.1:8b
- qwen3:4b
- qwen3:8b
- deepseek-r1:8b
- gemma3:4b
- gemma2:2b
- qwen2.5:7b

---

## 🚀 Llama 3.1:8b 系列 (7個)

| 模型名稱 | RAG策略 | 特色 | 適用場景 |
|---------|---------|------|---------|
| **llama31-vector-rag** | vector_only | 🔍 純向量檢索 | 語義相似性查詢 |
| **llama31-graph-rag** | graph_only | 🕸️ 知識圖譜檢索 | 關係探索分析 |
| **llama31-hybrid-rag** | hybrid_balanced | ⚖️ 平衡混合策略 | 通用問答（推薦） |
| **llama31-advanced-rag** | advanced_rag | 🎯 多級檢索+重排序 | 複雜深度分析 |
| **llama31-agentic-rag** | agentic_rag | 🤖 智能代理推理 | 多步驟決策 |
| **llama31-self-rag** | self_rag | 🔄 自我反思迭代 | 高準確性查詢 |
| **llama31-naive-rag** | naive_rag | ⚡ 極速檢索 | 快速基礎問答 |

---

## 🇨🇳 Qwen3:4b 系列 (7個) - 中文優化

| 模型名稱 | RAG策略 | 特色 | 適用場景 |
|---------|---------|------|---------|
| **qwen3-vector-rag** | vector_only | 🔍 向量檢索+中文優化 | 中文語義查詢 |
| **qwen3-graph-rag** | graph_only | 🕸️ 圖譜檢索+中文優化 | 中文關係分析 |
| **qwen3-hybrid-rag** | hybrid_balanced | ⚖️ 混合策略+中文優化 | 日常中文問答 |
| **qwen3-advanced-rag** | advanced_rag | 🎯 深度檢索+中文優化 | 中文深度研究 |
| **qwen3-agentic-rag** | agentic_rag | 🤖 智能推理+中文優化 | 中文邏輯推理 |
| **qwen3-self-rag** | self_rag | 🔄 自我反思+中文優化 | 中文學術查詢 |
| **qwen3-naive-rag** | naive_rag | ⚡ 極速+中文優化 | 快速中文問答 |

---

## 🇨🇳 Qwen3:8b 系列 (7個) - 中文優化 8B參數

| 模型名稱 | RAG策略 | 特色 | 適用場景 |
|---------|---------|------|---------|
| **qwen3-8b-vector-rag** | vector_only | 🔍 向量檢索+8B | 高質量語義查詢 |
| **qwen3-8b-graph-rag** | graph_only | 🕸️ 圖譜檢索+8B | 複雜關係探索 |
| **qwen3-8b-hybrid-rag** | hybrid_balanced | ⚖️ 混合策略+8B | 通用中文問答 |
| **qwen3-8b-advanced-rag** | advanced_rag | 🎯 深度檢索+8B | 複雜中文分析 |
| **qwen3-8b-agentic-rag** | agentic_rag | 🤖 智能推理+8B | 複雜邏輯推理 |
| **qwen3-8b-self-rag** | self_rag | 🔄 自我反思+8B | 高準確性查詢 |
| **qwen3-8b-naive-rag** | naive_rag | ⚡ 極速+8B | 快速問答 |

---

## 🧠 DeepSeek-R1:8b 系列 (7個) - 推理專家

| 模型名稱 | RAG策略 | 特色 | 適用場景 |
|---------|---------|------|---------|
| **deepseek-vector-rag** | vector_only | 🔍 向量+推理 | 邏輯語義查詢 |
| **deepseek-graph-rag** | graph_only | 🕸️ 圖譜+推理 | 結構化推理 |
| **deepseek-hybrid-rag** | hybrid_balanced | ⚖️ 混合+推理 | 通用推理問答 |
| **deepseek-advanced-rag** | advanced_rag | 🎯 深度+推理 | 複雜邏輯分析 |
| **deepseek-agentic-rag** | agentic_rag | 🤖 代理+推理 | 多步驟推理 |
| **deepseek-self-rag** | self_rag | 🔄 反思+推理 | 自我驗證推理 |
| **deepseek-naive-rag** | naive_rag | ⚡ 極速+推理 | 快速推理問答 |

---

## ⚡ Gemma3:4b 系列 (7個) - 輕量快速

| 模型名稱 | RAG策略 | 特色 | 適用場景 |
|---------|---------|------|---------|
| **gemma3-vector-rag** | vector_only | 🔍 向量+輕量 | 快速語義查詢 |
| **gemma3-graph-rag** | graph_only | 🕸️ 圖譜+輕量 | 快速關係探索 |
| **gemma3-hybrid-rag** | hybrid_balanced | ⚖️ 混合+輕量 | 日常快速問答 |
| **gemma3-advanced-rag** | advanced_rag | 🎯 深度+輕量 | 資源受限分析 |
| **gemma3-agentic-rag** | agentic_rag | 🤖 代理+輕量 | 快速決策 |
| **gemma3-self-rag** | self_rag | 🔄 反思+輕量 | 快速驗證 |
| **gemma3-naive-rag** | naive_rag | ⚡ 極速+輕量 | 極速基礎問答 |

---

## 🎯 RAG策略說明

### 📚 7種RAG策略

| 策略ID | 顯示名稱 | 圖標 | 說明 | 最佳用途 |
|--------|---------|------|------|---------|
| **vector_only** | VectorRAG | 🔍 | 純向量檢索，基於語義相似度 | 相似內容搜索、語義匹配 |
| **graph_only** | GraphRAG | 🕸️ | 知識圖譜檢索，探索概念關係 | 關係分析、結構化查詢 |
| **hybrid_balanced** | HybridRAG | ⚖️ | 平衡混合策略，向量+全文 | 通用問答、日常使用（推薦） |
| **advanced_rag** | AdvancedRAG | 🎯 | 多級檢索與重排序 | 複雜分析、深度研究 |
| **agentic_rag** | AgenticRAG | 🤖 | 智能代理式推理，多步驟決策 | 複雜推理、多步分析 |
| **self_rag** | SelfRAG | 🔄 | 自我反思策略，迭代改進 | 質量保證、準確性驗證 |
| **naive_rag** | NaiveRAG | ⚡ | 最簡單策略，極速響應 | 快速查詢、簡單問答 |

---

## 💡 使用建議

### 🌟 推薦組合（按場景）

#### 1️⃣ **日常通用問答**
```
推薦: llama31-hybrid-rag
原因: 平衡性能與質量，適合大多數場景
```

#### 2️⃣ **中文藝術史查詢**
```
推薦: qwen3-8b-hybrid-rag
原因: 中文優化+8B參數+平衡策略
```

#### 3️⃣ **複雜深度分析**
```
推薦: deepseek-advanced-rag
原因: 推理能力強+多級檢索
```

#### 4️⃣ **關係探索查詢**
```
推薦: qwen3-8b-graph-rag
原因: 知識圖譜檢索+中文優化
```

#### 5️⃣ **極速響應需求**
```
推薦: gemma3-naive-rag
原因: 最輕量組合，極速響應
```

#### 6️⃣ **學術研究查詢**
```
推薦: llama31-self-rag
原因: 自我反思機制，高準確性
```

---

## 🔧 如何使用

### 在OpenWebUI中使用

1. **打開OpenWebUI**: http://localhost:8080
2. **刷新頁面**: 按 `Ctrl+Shift+R` 或 `Cmd+Shift+R`
3. **選擇模型**: 在模型下拉選單中選擇任一RAG組合模型
4. **開始對話**: 提出您的藝術史問題

### 示例查詢

```
模型: llama31-hybrid-rag
問題: 達文西的代表作品有哪些？

模型: qwen3-8b-graph-rag
問題: 達文西和米開朗基羅的關係是什麼？

模型: deepseek-advanced-rag
問題: 分析印象派對現代藝術的影響

模型: gemma3-naive-rag
問題: 什麼是文藝復興？
```

---

## 📈 性能對比

| 系列 | 參數量 | 速度 | 中文能力 | 推理能力 | 資源消耗 |
|------|--------|------|---------|---------|---------|
| **Llama 3.1:8b** | 8B | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | 4.9 GB |
| **Qwen3:4b** | 4B | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | 2.5 GB |
| **Qwen3:8b** | 8B | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 5.2 GB |
| **DeepSeek-R1:8b** | 8B | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 5.2 GB |
| **Gemma3:4b** | 4B | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | 3.3 GB |

---

## 🔗 相關服務

### 系統端點

- **OpenWebUI**: http://localhost:8080
- **RAG Manager**: http://localhost:8007
- **Neo4j瀏覽器**: http://localhost:7474
- **Ollama API**: http://localhost:11434

### 健康檢查

```bash
# 檢查所有服務
curl http://localhost:8007/health

# 查看可用模型
docker exec art-history-ollama ollama list

# 查看RAG模型數量
docker exec art-history-ollama ollama list | grep -c "rag"
```

---

## 🎨 系統架構

```
用戶提問
    ↓
OpenWebUI
    ↓
選擇 LLM+RAG 模型
    ↓
Ollama (載入模型)
    ↓
RAG Manager (檢索)
    ├─→ Neo4j (知識圖譜)
    └─→ ChromaDB (向量數據庫)
    ↓
LLM生成回答
    ↓
返回給用戶
```

---

## 📝 注意事項

1. **模型大小**:
   - 輕量級: Gemma3 (3.3 GB)
   - 中等: Qwen3:4b (2.5 GB), Llama3.1 (4.9 GB)
   - 大型: Qwen3:8b, DeepSeek (5.2 GB)

2. **中文查詢**: 優先使用 Qwen3 系列

3. **推理任務**: 優先使用 DeepSeek 系列

4. **快速響應**: 優先使用 Gemma3 或 naive_rag 策略

5. **關係查詢**: 優先使用 graph_rag 策略

---

## 🎉 完成狀態

✅ **35個RAG組合模型全部創建完成！**
✅ **所有模型已在Ollama中可用**
✅ **OpenWebUI可以直接選擇使用**
✅ **RAG Manager服務正常運行**
✅ **Neo4j知識圖譜完整 (4,946節點)**

---

**現在您可以在OpenWebUI中自由選擇任何LLM+RAG組合模型進行藝術史問答了！** 🎨✨
