# 使用 42 種 RAG+LLM 組合的完整指南

## ✅ 系統狀態確認

### 已完成的配置
- ✅ 整合服務運行正常，提供 42 個 RAG+LLM 組合
- ✅ OpenWebUI 已配置外部 API 連接
- ✅ 環境變數正確設置
- ✅ Neo4j: 1,359 件藝術品，269 位藝術家
- ✅ ChromaDB: 125 個向量

### 服務地址
- **OpenWebUI**: http://localhost:8080
- **RAG Manager**: http://localhost:8007
- **整合服務**: http://localhost:8009

---

## 🎯 在 OpenWebUI 中使用 42 種組合

### 步驟 1: 打開 OpenWebUI
瀏覽器訪問: **http://localhost:8080**

### 步驟 2: 查看可用模型
點擊界面 **左上角的模型選擇下拉菜單**，您應該看到：

#### A. Ollama 基礎模型（7個）
- llama3.1:8b
- llama3.1:70b
- qwen2.5:7b
- qwen2.5:14b
- gemma2:9b
- gemma2:27b
- mistral:7b

#### B. RAG 組合模型（42個）
- 🦙 Llama 3.1 8B + 🔍 向量RAG
- 🦙 Llama 3.1 8B + 🕸️ 圖譜RAG
- 🦙 Llama 3.1 8B + ⚖️ 混合RAG
- 🦙 Llama 3.1 8B + 🚀 高級RAG
- 🦙 Llama 3.1 8B + 🤖 代理RAG
- 🦙 Llama 3.1 8B + 🔄 自我RAG
- ... 等 42 種組合

### 步驟 3: 選擇並測試
1. 從下拉菜單選擇一個 RAG 組合模型
2. 輸入藝術史相關問題：
   - "Renaissance painting"
   - "baroque sculpture"
   - "impressionist art"
3. 查看回答和參考來源

---

## 📊 比較實驗設計

### 實驗 1: 相同 LLM，不同 RAG 策略

**固定模型**: Llama 3.1 8B
**變量**: RAG 策略

```
實驗組 1: llama3.1:8b@vector_only     (純向量檢索)
實驗組 2: llama3.1:8b@graph_only      (純圖譜檢索)
實驗組 3: llama3.1:8b@hybrid_balanced (混合檢索)
```

**測試問題**:
- "Renaissance painting"
- "baroque sculpture"
- "impressionist art"

**比較維度**:
- 檢索時間 (ms)
- 回答準確性 (1-10)
- 來源相關性 (1-10)
- 回答完整性 (1-10)

---

### 實驗 2: 相同 RAG，不同 LLM

**固定策略**: Hybrid Balanced
**變量**: LLM 模型

```
實驗組 1: llama3.1:8b@hybrid_balanced   (8B 參數)
實驗組 2: llama3.1:70b@hybrid_balanced  (70B 參數)
實驗組 3: qwen2.5:14b@hybrid_balanced   (14B 參數)
```

**比較維度**:
- 生成質量
- 推理能力
- 回答流暢度
- 生成時間

---

### 實驗 3: 高級 RAG 策略對比

**測試複雜策略**:

```
實驗組 1: llama3.1:8b@advanced_rag  (多級檢索+重排序)
實驗組 2: llama3.1:8b@agentic_rag   (智能代理推理)
實驗組 3: llama3.1:8b@self_rag      (自我反思迭代)
```

**複雜問題**:
1. "Compare Renaissance and Baroque art styles"
2. "How did Renaissance influence modern art?"
3. "Differences between Italian and Northern Renaissance"

---

## 🔧 故障排除

### 如果看不到 RAG 組合模型

#### 1. 確認整合服務運行正常
```bash
curl http://localhost:8009/v1/models | jq '.data | length'
# 應該返回 42
```

#### 2. 檢查 OpenWebUI 環境變數
```bash
docker exec art-history-openwebui env | grep OPENAI_API
```
應該看到:
```
OPENAI_API_BASE_URLS=http://art-history-openwebui-integration:8009/v1
OPENAI_API_KEYS=sk-art-history-rag
```

#### 3. 重新加載界面
- 按 `Ctrl+Shift+R` 強制刷新瀏覽器
- 或清除緩存後重新訪問

#### 4. 手動添加連接（備用方法）

在 OpenWebUI 界面中:
1. 進入 **Settings** （設置）
2. 找到 **"Connections"** 或 **"外部連接"**
3. 添加新連接：
   - **Name**: Art History RAG
   - **API Base URL**: `http://art-history-openwebui-integration:8009/v1`
   - **API Key**: `sk-art-history-rag`
4. 保存並刷新

---

## 📈 實驗結果記錄模板

```markdown
## 實驗記錄

### 基本信息
- **日期**: 2025-10-16
- **測試問題**: "Renaissance painting"
- **測試輪次**: 3

### 模型配置
| 組合 ID | LLM | RAG 策略 |
|---------|-----|---------|
| 1 | llama3.1:8b | vector_only |
| 2 | llama3.1:8b | graph_only |
| 3 | llama3.1:8b | hybrid_balanced |

### 性能指標

| 指標 | Vector Only | Graph Only | Hybrid Balanced |
|------|-------------|------------|-----------------|
| 檢索時間 (ms) | 178 | 123 | 144 |
| 生成時間 (ms) | 1,315 | 1,170 | 2,372 |
| 來源數量 | 5 | 3 | 5 |
| 回答長度 (字符) | 583 | 450 | 620 |

### 質量評分 (1-10)

| 維度 | Vector Only | Graph Only | Hybrid Balanced |
|------|-------------|------------|-----------------|
| 相關性 | 8 | 7 | 9 |
| 準確性 | 7 | 8 | 9 |
| 完整性 | 7 | 6 | 9 |
| 流暢度 | 8 | 8 | 9 |

### 觀察與結論
- **Vector Only**: 檢索時間較長，找到更多語義相關的來源
- **Graph Only**: 速度最快，但來源較少，適合精確查詢
- **Hybrid Balanced**: 綜合表現最佳，平衡了速度和質量
```

---

## 🎯 推薦測試流程

### 階段 1: 基礎驗證 (15分鐘)
1. 選擇 `llama3.1:8b@hybrid_balanced`
2. 測試 3-5 個簡單問題
3. 確認系統返回來源和元數據

### 階段 2: RAG 策略對比 (30分鐘)
1. 固定 `llama3.1:8b`
2. 測試全部 6 種 RAG 策略
3. 記錄性能和質量指標

### 階段 3: LLM 模型對比 (45分鐘)
1. 固定 `hybrid_balanced` 策略
2. 測試 7 個不同 LLM
3. 比較生成質量和速度

### 階段 4: 深度分析 (60分鐘)
1. 選擇 Top 3 組合
2. 使用複雜問題深度測試
3. 撰寫分析報告

---

## 📞 常見問題

### Q: 只看到 Ollama 模型，沒有 RAG 組合？
**A**: 檢查環境變數，確保 `OPENAI_API_BASE_URLS` 正確設置。執行：
```bash
docker exec art-history-openwebui env | grep OPENAI_API_BASE_URLS
```

### Q: 查詢返回 "沒有找到相關資料"？
**A**: 使用單字關鍵詞如 "Renaissance"、"baroque"。某些複雜查詢可能確實找不到匹配。

### Q: 響應時間很慢？
**A**:
- 首次查詢需要加載模型（較慢）
- 70B 模型比 8B 模型慢很多
- 向量檢索比圖譜檢索稍慢

### Q: 如何重新加載模型列表？
**A**:
1. 刷新瀏覽器（Ctrl+Shift+R）
2. 或重啟 OpenWebUI: `docker restart art-history-openwebui`

---

## 🛠️ 服務管理命令

```bash
# 查看所有容器狀態
docker ps --filter "name=art-history"

# 重啟 OpenWebUI
docker restart art-history-openwebui

# 查看整合服務日誌
docker logs art-history-openwebui-integration --tail 50

# 測試 RAG Manager
curl http://localhost:8007/health

# 測試整合服務
curl http://localhost:8009/health

# 測試模型列表
curl http://localhost:8009/v1/models | jq '.data | length'
```

---

## 🎉 開始您的實驗！

系統已經完全配置好，您現在可以：

1. ✅ 打開 http://localhost:8080
2. ✅ 在模型下拉菜單中選擇任一 RAG 組合
3. ✅ 開始您的比較實驗

**祝實驗順利！** 🚀

---

## 📚 技術文檔

詳細的技術文檔請參考：
- `setup_openwebui_models.md` - 詳細配置說明
- `langchain-rag/rag_config.json` - 所有模型配置
- Docker logs - 運行狀態和錯誤信息
