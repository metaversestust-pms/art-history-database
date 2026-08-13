# 🔍 藝術史資料庫 - RAG 方法完整總覽

**生成時間**: 2025-10-15
**系統版本**: v3.0

---

## 📊 系統 RAG 方法總覽

您的藝術史資料庫系統目前整合了 **10 種不同的 RAG 方法**，除了 GraphRAG 之外還有 9 種。

---

## 🎯 所有 RAG 方法詳細說明

### 1. ⚡ Naive RAG (最簡單策略)

**實現文件**:
- `integrated_rag_optimizer.py` (_naive_rag_query 方法)
- `enhanced_openwebui_rag_function_v3.py`

**特點**:
- 最簡單的檢索增強生成
- 基於關鍵詞匹配
- 極速響應 (~0.05秒)
- 適合簡單查詢和快速答案

**技術細節**:
```python
- 關鍵詞提取：基於分詞和長度過濾
- 檢索方法：簡單文本匹配
- 置信度：0.5 (較低)
- 處理時間：最快
```

**適用場景**:
- 簡單問答
- 快速查詢
- 基礎關鍵詞搜索
- 需要極速響應的場景

---

### 2. 🔍 Vector RAG (向量檢索)

**實現文件**:
- `integrated_rag_optimizer.py` (_vector_only_query 方法)
- `rag_strategy_server.py`
- `src/agents/rag/vector_rag_agent.py`

**特點**:
- 純向量相似度檢索
- 基於語義理解
- 適合內容相似性查詢
- 使用 BGE-M3 embedding 模型

**技術細節**:
```python
- Embedding 模型：bge-m3 (1024維)
- 向量資料庫：ChromaDB
- 相似度計算：餘弦相似度
- Top-K 檢索：可配置 (預設10)
- 置信度：0.8-0.85
```

**適用場景**:
- 語義搜索
- 內容相似度匹配
- 描述性查詢
- 主題相關文檔檢索

**配置位置**: `.env` 中 `TEXT_EMBEDDING_MODEL=BGE-M3`

---

### 3. 🕸️ Graph RAG (知識圖譜檢索)

**實現文件**:
- `neo4j_graph_rag_server.py` (專門服務器)
- `integrated_rag_optimizer.py` (_graph_only_query 方法)
- `langchain-rag/knowledge_graph_rag.py`

**特點**:
- 基於 Neo4j 知識圖譜
- 實體關係檢索
- 結構化查詢
- 探索概念關係

**技術細節**:
```python
- 知識圖譜：Neo4j (2,281 nodes, 2,706 relationships)
- 查詢語言：Cypher
- 實體類型：Artwork, Artist, Museum, Period
- 關係類型：CREATED, HOUSED_IN, FROM_PERIOD
- 置信度：0.85-0.95
```

**適用場景**:
- 關係分析
- 結構化查詢
- 實體連結探索
- 藝術史脈絡研究

**專用 API**: http://localhost:8008

---

### 4. ⚖️ Hybrid Balanced RAG (混合平衡策略)

**實現文件**:
- `integrated_rag_optimizer.py` (_hybrid_balanced_query 方法)
- `rag_strategy_server.py`

**特點**:
- 結合向量和圖譜檢索
- 平衡兩種方法優勢
- 適合大多數查詢
- 並行執行雙重檢索

**技術細節**:
```python
- 向量權重：0.6 (可配置)
- 圖譜權重：0.4 (可配置)
- 執行方式：並行 (asyncio.gather)
- 結果融合：加權合併
- 置信度：0.8-0.9 (加權平均)
```

**適用場景**:
- 通用查詢
- 需要全面檢索
- 不確定查詢類型
- 追求最佳綜合效果

**配置**:
```python
RAG_FUSION_WEIGHTS=vector:0.4,graph:0.3,keyword:0.3
```

---

### 5. 🎯 Advanced RAG (高級策略)

**實現文件**:
- `integrated_rag_optimizer.py` (_advanced_rag_query 方法)
- `enhanced_openwebui_rag_function_v3.py`

**特點**:
- 多級檢索與重排序
- 查詢擴展
- 深度分析
- 三階段檢索流程

**技術細節**:
```python
階段1：粗檢索 (向量 + 圖譜)
階段2：擴展檢索 (基於初始結果擴展)
階段3：重排序和融合 (相關性 + 多樣性)

特性：
- 查詢擴展：自動添加相關概念
- 重排序：基於相關性分數
- Top-K：8 個結果 (可配置)
- 置信度提升：1.15x
- 處理時間：~0.2秒
```

**適用場景**:
- 複雜分析查詢
- 深度研究
- 學術性問題
- 需要高質量結果

---

### 6. 🔄 Self-RAG (自我反思策略)

**實現文件**:
- `integrated_rag_optimizer.py` (_self_rag_query 方法)
- `enhanced_openwebui_rag_function_v3.py`

**特點**:
- 自我評估和改進
- 迭代優化答案
- 質量保證機制
- 多輪檢索和驗證

**技術細節**:
```python
工作流程：
1. 初始檢索 (Hybrid Balanced)
2. 自我評估 (完整性、相關性、覆蓋度)
3. 質量判斷 (閾值: 0.75)
4. 改進檢索 (如果質量不足)
5. 結果融合與去重

評估指標：
- 完整性評分：基於來源數量
- 相關性評分：置信度分數
- 覆蓋度評分：檢索方法多樣性
- 處理時間：~0.25秒
```

**適用場景**:
- 質量要求高
- 準確性驗證
- 需要可靠答案
- 學術研究

---

### 7. 🤖 Agentic RAG (智能代理策略)

**實現文件**:
- `integrated_rag_optimizer.py` (_agentic_rag_query 方法)
- `enhanced_openwebui_rag_function_v3.py`

**特點**:
- 智能代理式推理
- 多步驟決策
- 問題分解和規劃
- 自主選擇最佳策略

**技術細節**:
```python
四階段流程：

階段1：問題分析
- 意圖識別 (factual/analytical)
- 複雜度評估
- 領域關鍵詞提取
- 推理需求判斷

階段2：策略決策
- 事實性 → Vector RAG
- 推理性 → Graph RAG
- 複雜性 → Hybrid RAG

階段3：知識增強
- 初始檢索
- 補充檢索 (如需要)
- 結果驗證

階段4：推理生成
- 多重推理步驟
- 智能答案合成
- 置信度增強 (+0.1-0.15)
- 處理時間：~0.3秒
```

**適用場景**:
- 複雜推理問題
- 多步分析
- 智能決策需求
- 自適應查詢處理

---

### 8. 🎨 Adaptive RAG (自適應策略)

**實現文件**:
- `integrated_rag_optimizer.py` (_adaptive_query 方法)
- `langchain-rag/adaptive_rag.py`

**特點**:
- 基於歷史性能自動選擇
- 機器學習優化
- 動態策略調整
- 持續改進

**技術細節**:
```python
決策機制：
- 監控所有策略性能
- 計算綜合評分 (成功率70% + 速度30%)
- 動態選擇最佳策略
- 實時性能統計

性能跟蹤：
- 查詢次數
- 平均處理時間
- 成功率 (基於置信度)
- 自適應學習歷史
```

**適用場景**:
- 長期運行系統
- 需要自動優化
- 不同類型查詢混合
- 追求最佳效能

---

### 9. 🔧 Specialized RAG (專門化策略)

**實現文件**:
- `integrated_rag_optimizer.py` (_specialized_query 方法)
- `rag_strategy_server.py`

**特點**:
- 基於查詢類型自動選擇
- 規則導向
- 針對性優化
- 智能路由

**技術細節**:
```python
路由規則：

關係查詢 → Graph RAG
- 關鍵詞：影響、師承、關係、influence
- 例如："哪些藝術家影響了畢卡索？"

內容查詢 → Vector RAG
- 關鍵詞：描述、內容、特色、describe
- 例如："描述文藝復興的藝術特色"

其他查詢 → Hybrid Balanced
- 不確定類型
- 綜合性問題
```

**適用場景**:
- 明確查詢意圖
- 特定領域專業化
- 需要最優單一策略
- 規則可預測場景

---

### 10. 🌈 Multimodal RAG (多模態檢索)

**實現文件**:
- `langchain-rag/multimodal_rag.py`
- `deploy-multimodal-rag.py`
- `rag-system-config.yaml`

**特點**:
- 文本 + 圖像聯合檢索
- 跨模態對齊
- CLIP 圖像編碼
- 晚期融合策略

**技術細節**:
```yaml
配置 (rag-system-config.yaml):
  enabled: true
  text_weight: 0.6
  image_weight: 0.4
  image_processor_url: http://localhost:8080
  clip_model: clip-vit-base-patch32
  fusion_strategy: late_fusion

模型：
  - 文本：BGE-M3 (1024維)
  - 圖像：CLIP ViT-B/32
  - GPU 加速：CUDA 支援
```

**適用場景**:
- 藝術作品圖像搜索
- 文字描述匹配圖像
- 視覺藝術分析
- 跨模態檢索

**ML 服務**: http://localhost:8080

---

## 📈 RAG 方法比較表

| RAG 方法 | 處理速度 | 準確度 | 複雜度 | 資源消耗 | 適用場景 |
|---------|---------|--------|--------|----------|----------|
| **Naive RAG** | ⚡⚡⚡⚡⚡ | ⭐⭐ | 低 | 極低 | 簡單快速查詢 |
| **Vector RAG** | ⚡⚡⚡⚡ | ⭐⭐⭐⭐ | 中 | 中 | 語義相似搜索 |
| **Graph RAG** | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ | 中高 | 中 | 關係結構查詢 |
| **Hybrid Balanced** | ⚡⚡⚡ | ⭐⭐⭐⭐ | 中 | 中高 | 通用平衡查詢 |
| **Advanced RAG** | ⚡⚡ | ⭐⭐⭐⭐⭐ | 高 | 高 | 深度分析研究 |
| **Self-RAG** | ⚡⚡ | ⭐⭐⭐⭐⭐ | 高 | 高 | 質量保證需求 |
| **Agentic RAG** | ⚡⚡ | ⭐⭐⭐⭐⭐ | 極高 | 高 | 智能推理決策 |
| **Adaptive RAG** | ⚡⚡⚡ | ⭐⭐⭐⭐ | 中 | 中 | 長期自動優化 |
| **Specialized RAG** | ⚡⚡⚡⚡ | ⭐⭐⭐⭐ | 中 | 中 | 特定類型查詢 |
| **Multimodal RAG** | ⚡⚡ | ⭐⭐⭐⭐⭐ | 極高 | 極高 | 圖像文本聯合 |

---

## 🔧 RAG 方法配置位置

### 環境變量配置 (`.env`)

```bash
# RAG 框架啟用
RAG_FRAMEWORKS_ENABLED=advanced,vector,multilingual,graph,self-reflection
DEFAULT_RAG_FRAMEWORK=vector

# 混合 RAG 權重
RAG_FUSION_WEIGHTS=vector:0.4,graph:0.3,keyword:0.3

# 向量資料庫
CHROMADB_HOST=localhost
CHROMADB_PORT=8001
TEXT_EMBEDDING_MODEL=BGE-M3

# 知識圖譜
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=arthistory123

# 多模態
MULTIMODAL_FUSION_ENABLED=true
```

### 系統配置文件 (`rag-system-config.yaml`)

```yaml
rag_systems:
  basic_text_rag:
    enabled: true
    embedding_model: "bge-m3"
    chunk_size: 512
    top_k_retrieval: 5
    rerank: true

  multimodal_rag:
    enabled: true
    text_weight: 0.6
    image_weight: 0.4
    fusion_strategy: "late_fusion"

  expert_domain_rag:
    enabled: true
    knowledge_graphs: true
    entity_extraction: true
```

---

## 🚀 RAG 服務器端點

### 1. Graph RAG Server
- **地址**: http://localhost:8008
- **方法**: Graph RAG
- **實現**: `neo4j_graph_rag_server.py`
- **端點**: `/query`, `/health`, `/stats`

### 2. RAG Strategy Server
- **地址**: http://localhost:8006
- **方法**: 所有策略 (通過 integrated_rag_optimizer)
- **實現**: `rag_strategy_server.py`
- **端點**: `/query`, `/strategies`, `/batch_query`

### 3. Unified RAG Manager
- **地址**: http://localhost:8002
- **方法**: 統一管理所有 RAG
- **實現**: `unified_rag_manager.py`
- **端點**: `/query`, `/system/status`, `/system/optimize`

---

## 💡 使用建議

### 根據任務選擇 RAG 方法

1. **快速查詢** → Naive RAG
   ```
   "梵谷是誰？"
   "印象派定義"
   ```

2. **語義搜索** → Vector RAG
   ```
   "類似蒙娜麗莎風格的作品"
   "文藝復興時期的肖像畫特點"
   ```

3. **關係探索** → Graph RAG
   ```
   "畢卡索受哪些藝術家影響？"
   "巴洛克藝術家之間的師承關係"
   ```

4. **通用查詢** → Hybrid Balanced
   ```
   "介紹印象派藝術運動"
   "達芬奇的主要作品"
   ```

5. **深度研究** → Advanced RAG
   ```
   "分析文藝復興與巴洛克的藝術風格演變"
   "比較東西方繪畫技法的異同"
   ```

6. **質量保證** → Self-RAG
   ```
   學術論文研究
   重要決策參考
   ```

7. **複雜推理** → Agentic RAG
   ```
   "為什麼梵谷的作品在死後才被認可？"
   "如何理解印象派對現代藝術的影響？"
   ```

8. **圖像相關** → Multimodal RAG
   ```
   "找到類似這張畫的作品"（上傳圖片）
   "這幅畫的風格分析"（圖像輸入）
   ```

---

## 🔄 RAG 方法切換

### 在 OpenWebUI 中

OpenWebUI Function v3 支持 **5 種 LLM × 7 種 RAG = 35 種組合**：

```
模型選擇格式：
- llama3-1-8b-basic_rag      (Llama3.1 + 基礎RAG)
- llama3-1-8b-graph_rag      (Llama3.1 + GraphRAG)
- llama3-1-8b-advanced_rag   (Llama3.1 + Advanced RAG)
- llama3-1-8b-agentic_rag    (Llama3.1 + Agentic RAG)
- llama3-1-8b-self_rag       (Llama3.1 + Self-RAG)
- gemma3-4b-vector_rag       (Gemma3 + Vector RAG)
- qwen3-4b-naive_rag         (Qwen3 + Naive RAG)
... 等共 35 種組合
```

### 通過 API

```bash
# Graph RAG
curl -X POST http://localhost:8008/query \
  -H "Content-Type: application/json" \
  -d '{"query": "your question", "strategy": "graph_only"}'

# 其他策略
curl -X POST http://localhost:8006/query \
  -H "Content-Type: application/json" \
  -d '{"query": "your question", "strategy": "advanced_rag"}'

# 統一管理
curl -X POST http://localhost:8002/query \
  -H "Content-Type: application/json" \
  -d '{"query": "your question", "strategy": "self_rag"}'
```

### 通過 Python

```python
from integrated_rag_optimizer import IntegratedRAGOptimizer, RAGStrategy

# 初始化
optimizer = IntegratedRAGOptimizer()
optimizer.initialize_components()

# 使用不同策略
result = await optimizer.query(
    "梵谷的向日葵",
    strategy="graph_only"  # 或 "vector_only", "advanced_rag" 等
)

print(result.answer)
print(f"信心分數: {result.confidence_score}")
```

---

## 📊 性能監控

所有 RAG 方法都集成了性能監控：

```python
# 查看策略性能
status = optimizer.get_system_status()
print(status['strategy_performance'])

# 輸出範例：
{
  'vector_only': {'count': 45, 'avg_time': 0.12, 'success_rate': 0.87},
  'graph_only': {'count': 38, 'avg_time': 0.15, 'success_rate': 0.92},
  'hybrid_balanced': {'count': 67, 'avg_time': 0.18, 'success_rate': 0.89},
  ...
}
```

---

## 🎯 總結

您的藝術史資料庫擁有**業界最完整的 RAG 方法集合**：

✅ **10 種 RAG 方法** - 從最簡單到最先進
✅ **3 個專用服務器** - Graph RAG, Strategy Server, Unified Manager
✅ **35 種 LLM×RAG 組合** - 5 種模型 × 7 種策略
✅ **自動性能優化** - Adaptive 和 Self-RAG 機制
✅ **完整監控體系** - 實時性能追蹤和統計
✅ **靈活配置** - 環境變量和 YAML 配置支持

### 推薦使用順序

1. **初學者**: Hybrid Balanced → 平衡效果，適合大多數場景
2. **進階用戶**: 根據任務選擇 Vector/Graph/Advanced
3. **專業研究**: Self-RAG 或 Agentic RAG → 最高質量
4. **系統優化**: Adaptive RAG → 長期自動優化

---

**文檔生成時間**: 2025-10-15
**系統版本**: Art History Database v3.0
**支援**: 查看 `GRAPH_RAG_SETUP_GUIDE.md` 和 `rag-system-config.yaml`

🎨 祝您使用愉快！
