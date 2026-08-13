# 檢索排序機制分析與優化方案

## 當前排序機制分析

### 1. Vector-only 策略 (query_vector_only)
**現狀：**
- 直接使用 ChromaDB 返回的結果（按 L2 距離排序）
- 相似度分數已優化（指數衰減，scaling_factor=30）
- 沒有額外的重排序

**優點：**
- 簡單快速
- 向量相似度計算準確

**缺點：**
- 只考慮語義相似度
- 忽略實體重要性、時間相關性等因素

### 2. Graph-only 策略 (query_graph_only)
**現狀：**
- 基於關鍵詞精確匹配查詢圖譜
- 所有結果分配固定分數 0.9（line 156）
- 沒有細粒度的相關性排序

**優點：**
- 精確匹配實體
- 利用圖譜關係

**缺點：**
- 缺乏相關性排序算法
- 無法區分結果質量
- 沒有文本相似度計算

### 3. Hybrid 策略 (query_hybrid)
**現狀：**
- 圖譜結果基礎分數：0.7
- 向量結果基礎分數：vector_score * 0.8
- 雙重匹配：min(0.95, 0.7 + vector_score * 0.3)
- 按綜合分數降序排序

**優點：**
- 結合圖譜和向量優勢
- 獎勵雙重匹配結果

**缺點：**
- 分數融合權重較為主觀
- 沒有分數歸一化
- 缺乏多樣性考慮

## 優化方案

### 階段 1：實現 BM25 文本相關性排序

**目標：** 為圖譜查詢結果添加基於 BM25 的相關性分數

**實現：**
```python
def calculate_bm25_score(query_terms, document, k1=1.5, b=0.75):
    """計算 BM25 分數"""
    # 文檔長度、詞頻統計
    # 計算 IDF 和 TF
    # 返回 BM25 分數
```

**應用場景：**
- graph_only 策略：對 artworks 結果排序
- hybrid 策略：圖譜結果使用 BM25 分數而非固定 0.7

### 階段 2：優化 Hybrid 分數融合機制

**改進點：**
1. **分數歸一化：** 將圖譜和向量分數歸一化到 [0, 1]
2. **動態權重：** 根據查詢類型調整融合權重
3. **融合公式：** 使用加權調和平均或線性組合

**公式：**
```python
# 線性組合
final_score = α * graph_score + β * vector_score

# 調和平均（強調一致性）
final_score = 2 * (graph_score * vector_score) / (graph_score + vector_score)

# 加權幾何平均
final_score = (graph_score^α * vector_score^β)^(1/(α+β))
```

### 階段 3：添加結果多樣性去重

**目標：** 避免返回過於相似的結果

**方法：**
1. **MMR (Maximal Marginal Relevance)：**
   - 平衡相關性和多樣性
   - MMR = λ * relevance - (1-λ) * max_similarity_to_selected

2. **基於藝術家/時期的多樣性：**
   - 限制同一藝術家/時期的作品數量
   - 優先展示不同藝術家的代表作

### 階段 4：考慮實體重要性

**重要性指標：**
1. **藝術家重要性：**
   - 作品數量（artwork_count）
   - 館藏分布（博物館數量）

2. **作品重要性：**
   - 收藏館地位（羅浮宮、大都會等）
   - 描述長度（通常重要作品描述更詳細）

**實現：**
```python
def calculate_entity_importance(entity_data):
    """計算實體重要性分數"""
    importance = 0.0

    # 藝術家作品數量
    if 'artwork_count' in entity_data:
        importance += min(1.0, entity_data['artwork_count'] / 50)

    # 館藏地位
    prestigious_museums = ['Louvre', 'Metropolitan', 'Vatican', 'Uffizi']
    if entity_data.get('museum') in prestigious_museums:
        importance += 0.3

    return min(1.0, importance)
```

### 階段 5：整合排序流程

**最終排序公式：**
```python
final_score = (
    relevance_score * 0.6 +      # 相關性（BM25 或向量）
    importance_score * 0.3 +     # 實體重要性
    diversity_penalty * 0.1      # 多樣性調整
)
```

## 測試計畫

1. **A/B 測試：** 對比優化前後的排序質量
2. **評估指標：**
   - NDCG (Normalized Discounted Cumulative Gain)
   - MRR (Mean Reciprocal Rank)
   - 用戶滿意度（人工評估）
3. **測試查詢集：** 使用現有的 25 個綜合測試查詢

## 實施順序

1. ✅ 分析當前排序機制
2. 🔄 實現 BM25 文本相關性排序
3. ⏳ 優化 hybrid 分數融合
4. ⏳ 添加多樣性去重
5. ⏳ 考慮實體重要性
6. ⏳ 測試與評估
