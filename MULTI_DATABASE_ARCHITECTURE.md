# 🗄️ 多資料庫 RAG 架構設計文檔

文檔版本: v1.0
創建時間: 2025-10-19
狀態: 設計中

---

## 📊 現有資料庫分析

### 1. Neo4j 圖資料庫

**用途**: 知識圖譜、關係推理

**現有數據**:
- 總節點: 4,946
- 總關係: 5,616
- 向量嵌入: 2,310 個（760藝術家 + 1,550作品）
- 覆蓋率: 50%+

**優勢**:
- ✅ 知識圖譜關係（藝術家-作品-博物館-時期）
- ✅ Cypher 複雜查詢
- ✅ 圖遍歷和推理
- ✅ 結構化元數據

**適用RAG策略**:
- **Graph RAG** ⭐⭐⭐⭐⭐ (主要)
- **Enhanced RAG** ⭐⭐⭐⭐ (混合檢索)
- **Hybrid RAG** ⭐⭐⭐⭐ (混合檢索)

**數據來源**:
- WikiArt API
- Met Museum API
- 自定義爬蟲數據

### 2. ChromaDB 向量資料庫

**用途**: 純向量語義搜索

**現有數據**:
- 總向量: 1,441 個
- 中文標籤: 1,376 個 (95.5%)
- 模型: nomic-embed-text

**優勢**:
- ✅ 極快的向量搜索
- ✅ 豐富的中文標籤
- ✅ 完整的元數據
- ✅ 易於擴展

**適用RAG策略**:
- **Vector RAG** ⭐⭐⭐⭐⭐ (主要)
- **Advanced RAG** ⭐⭐⭐⭐ (向量檢索)
- **Agentic RAG** ⭐⭐⭐⭐ (向量檢索)
- **Self RAG** ⭐⭐⭐⭐ (向量檢索)
- **Naive RAG** ⭐⭐⭐⭐ (簡單向量)

**數據來源**:
- enhanced_renaissance_baroque_*.json
- enhanced_masterpieces_curated.json
- 爬蟲增強數據

### 3. 建議新增：PostgreSQL (可選)

**用途**: 關聯式資料庫、全文搜索

**計劃數據**:
- 書籍資料
- 作者資料
- 文獻引用

**優勢**:
- ✅ pgVector 向量支持
- ✅ 全文搜索
- ✅ 複雜關聯查詢
- ✅ ACID 保證

**適用場景**:
- 學術文獻檢索
- 書籍引用查詢
- 結構化資料查詢

---

## 🏗️ 多資料源 RAG 整合架構

### 架構圖

```
使用者查詢
    ↓
OpenWebUI
    ↓
RAG 策略路由器 (新建)
    ↓
┌─────────────┬──────────────┬─────────────┐
│   Neo4j     │   ChromaDB   │ PostgreSQL  │
│ (圖譜+向量) │   (純向量)   │ (關聯+文獻) │
└─────────────┴──────────────┴─────────────┘
    ↓            ↓            ↓
資料源聚合器
    ↓
結果重排序 (Re-ranker)
    ↓
LLM (Ollama)
    ↓
帶來源標註的回答
```

### 策略-資料源映射表

| RAG 策略 | 主要資料源 | 輔助資料源 | 資料來源標註 |
|---------|-----------|-----------|------------|
| **Enhanced RAG** | Neo4j (向量+全文+圖) | ChromaDB | neo4j, chromadb |
| **Vector RAG** | ChromaDB | Neo4j | chromadb, neo4j |
| **Graph RAG** | Neo4j | - | neo4j |
| **Hybrid RAG** | Neo4j + ChromaDB | - | neo4j, chromadb |
| **Advanced RAG** | ChromaDB | Neo4j | chromadb, neo4j |
| **Agentic RAG** | ChromaDB | Neo4j | chromadb, neo4j |
| **Self RAG** | ChromaDB | Neo4j | chromadb, neo4j |
| **Naive RAG** | ChromaDB | - | chromadb |

---

## 💡 資料來源追蹤設計

### 1. 元數據結構

每個檢索結果包含完整來源信息：

```json
{
  "content": "...",
  "score": 0.85,
  "retrieval_method": "vector",
  "source_database": "chromadb",  // 新增
  "source_collection": "art_history_collection",  // 新增
  "source_type": "artwork",  // 新增
  "original_source": "Met Museum API",  // 新增
  "source_url": "https://...",  // 新增
  "ingested_at": "2025-10-19T...",  // 新增
  "metadata": {
    "title": "...",
    "artist": "...",
    "date": "...",
    ...
  }
}
```

### 2. 來源標註格式

**在回答中顯示**:

```
達文西的《蒙娜麗莎》創作於1503-1519年間，是文藝復興時期的代表作...

---
📚 參考資料:
1. 蒙娜麗莎 - Leonardo da Vinci, 1503-1519
   來源: ChromaDB > art_history_collection > Met Museum API
   相關度: 0.92 | 檢索方法: vector

2. Leonardo da Vinci (藝術家)
   來源: Neo4j > Artist節點 > WikiArt
   相關度: 0.88 | 檢索方法: graph_traversal

3. 文藝復興時期繪畫特色
   來源: Neo4j > Period節點 > 內部知識庫
   相關度: 0.85 | 檢索方法: fulltext

📊 檢索統計:
- ChromaDB: 2 個結果
- Neo4j: 3 個結果
- 檢索時間: 0.15秒
```

---

## 🔧 實施方案

### 階段一：資料源路由器（立即）

**文件**: `multi_database_router.py`

**功能**:
1. 根據RAG策略選擇資料源
2. 並行查詢多個資料庫
3. 統一結果格式
4. 添加來源追蹤

**API**:
```python
router.route_query(
    query="達文西",
    strategy="hybrid_balanced",
    top_k=5
) -> List[Document]
```

### 階段二：ChromaDB 整合（今天）

**任務**:
1. ✅ ChromaDB已有1,441個向量
2. 創建ChromaDB檢索器
3. 集成到RAG服務器
4. 測試向量檢索

**預期效果**:
- Vector RAG 使用ChromaDB
- 中文查詢準確度 +30%

### 階段三：來源追蹤（本週）

**任務**:
1. 為Neo4j結果添加來源元數據
2. 為ChromaDB結果添加原始來源
3. 更新OpenWebUI顯示格式
4. 創建來源統計

### 階段四：PostgreSQL 擴展（可選）

**任務**:
1. 設置PostgreSQL + pgVector
2. 導入書籍和文獻資料
3. 創建PostgreSQL檢索器
4. 集成到路由器

---

## 📋 資料擴增策略

### 1. 現有資料補充

**Neo4j 優化**:
```bash
# 補充中文名稱
python add-chinese-names-to-neo4j.py

# 補充作品描述
python enhance-artwork-descriptions.py

# 添加資料來源標記
python tag-data-sources.py
```

**ChromaDB 優化**:
```bash
# 持續導入新爬取的數據
node integrate-to-chromadb.js

# 更新向量（新模型）
python update-chromadb-embeddings.py
```

### 2. 新資料來源

**計劃整合**:
- [ ] Google Arts & Culture API
- [ ] Europeana API
- [ ] 大英博物館 API
- [ ] 羅浮宮 API
- [ ] 台北故宮數位典藏

**資料類型**:
- 作品高清圖片
- 藝術家傳記
- 展覽資訊
- 學術論文摘要

### 3. 爬蟲系統整合

**現有爬蟲**:
```
data/enhanced/
├─ enhanced_renaissance_baroque_*.json (6個文件)
└─ enhanced_masterpieces_curated.json
```

**自動化流程**:
1. 爬蟲獲取新數據 → JSON
2. 數據增強（中文標籤） → enhanced_*.json
3. 並行導入：
   - → Neo4j (圖結構)
   - → ChromaDB (向量)
   - → PostgreSQL (關聯)

---

## 🎯 預期改進效果

### 檢索準確度

| 查詢類型 | 當前（單一Neo4j） | 優化後（多資料源） | 改進 |
|---------|-----------------|------------------|------|
| 中文藝術家 | 60-70% | 85-95% | **+30%** |
| 中文作品 | 50-60% | 80-90% | **+50%** |
| 時期風格 | 70-80% | 90-95% | **+20%** |
| 複雜查詢 | 65-75% | 85-92% | **+25%** |

### 資料覆蓋

| 資料類型 | 當前 | 優化後 | 增加 |
|---------|-----|--------|------|
| 作品 | 3,176 (Neo4j) | 4,617+ | +45% |
| 藝術家 | 1,499 (Neo4j) | 2,000+ | +33% |
| 中文標籤 | 少量 | 3,800+ | **+800%** |
| 資料來源 | 單一 | 多元 | 可追蹤 |

### 用戶體驗

**優化前**:
```
回答: ...（基於Neo4j數據）
來源: Neo4j（不明確）
```

**優化後**:
```
回答: ...（融合多個來源）
來源:
- Met Museum (ChromaDB) - 權威
- WikiArt (Neo4j) - 圖譜
- 內部知識庫 (Neo4j) - 關係
清楚標示每個事實的出處
```

---

## 🔍 技術細節

### 1. 資料源選擇邏輯

```python
def select_datasources(strategy: str) -> List[str]:
    """根據策略選擇資料源"""
    mapping = {
        "enhanced_rag": ["neo4j", "chromadb"],
        "vector_only": ["chromadb", "neo4j"],
        "graph_only": ["neo4j"],
        "hybrid_balanced": ["neo4j", "chromadb"],
        "advanced_rag": ["chromadb", "neo4j"],
        "agentic_rag": ["chromadb", "neo4j"],
        "self_rag": ["chromadb", "neo4j"],
        "naive_rag": ["chromadb"]
    }
    return mapping.get(strategy, ["neo4j"])
```

### 2. 並行查詢

```python
async def parallel_query(query: str, sources: List[str]):
    """並行查詢多個資料源"""
    tasks = []

    if "neo4j" in sources:
        tasks.append(query_neo4j(query))
    if "chromadb" in sources:
        tasks.append(query_chromadb(query))
    if "postgres" in sources:
        tasks.append(query_postgres(query))

    results = await asyncio.gather(*tasks)
    return merge_results(results)
```

### 3. 結果融合

```python
def merge_results(results: List[List[Document]]) -> List[Document]:
    """融合多資料源結果"""
    merged = []

    # 1. 收集所有結果
    for source_results in results:
        merged.extend(source_results)

    # 2. 去重（基於內容相似度）
    unique = deduplicate(merged)

    # 3. 重排序（融合分數）
    reranked = rerank(unique)

    # 4. 保留來源信息
    return reranked
```

---

## 📊 監控與評估

### 1. 資料源使用統計

```python
{
    "query_count": {
        "neo4j": 1234,
        "chromadb": 2345,
        "postgres": 567
    },
    "avg_response_time": {
        "neo4j": 0.15,
        "chromadb": 0.05,
        "postgres": 0.08
    },
    "hit_rate": {
        "neo4j": 0.85,
        "chromadb": 0.92,
        "postgres": 0.78
    }
}
```

### 2. 來源品質評分

- Met Museum: 0.95 (權威度)
- WikiArt: 0.90 (完整度)
- 內部知識庫: 0.85 (關聯度)

---

## 🚀 實施時間表

### 第1天（今天）
- [x] 分析現有資料庫架構
- [x] 設計多資料源整合方案
- [ ] 創建資料源路由器 v1.0
- [ ] 測試ChromaDB檢索

### 第2-3天
- [ ] 完善來源追蹤
- [ ] 更新OpenWebUI顯示
- [ ] 優化結果融合算法
- [ ] 性能測試

### 第1週
- [ ] 為Neo4j數據添加來源標記
- [ ] 持續爬取新數據
- [ ] 建立自動化導入流程
- [ ] 文檔完善

### 第2週（可選）
- [ ] PostgreSQL設置
- [ ] 文獻資料導入
- [ ] 高級查詢優化

---

## 💡 最佳實踐

### 1. 資料一致性

- 定期同步Neo4j和ChromaDB
- 使用統一的ID系統
- 版本控制資料更新

### 2. 性能優化

- 並行查詢多資料源
- 結果快取
- 資料庫連接池

### 3. 品質保證

- 資料源可靠性評分
- 結果驗證機制
- 用戶反饋收集

---

## 📚 參考資料

- [LangChain Multi-Vector Retriever](https://python.langchain.com/docs/modules/data_connection/retrievers/multi_vector)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Neo4j Graph Data Science](https://neo4j.com/docs/graph-data-science/)

---

**文檔維護**: Claude Code
**最後更新**: 2025-10-19
**狀態**: 設計階段 → 實施中
