# 🚀 Graph RAG 快速開始指南

**建立時間**: 2025-10-15
**系統狀態**: ✅ 完全就緒

---

## ✅ 系統已完成設置

### 1. 服務狀態

| 服務 | 狀態 | 地址 |
|-----|------|------|
| **Neo4j 知識圖譜** | 🟢 運行中 | http://localhost:7474 |
| **Graph RAG API** | 🟢 運行中 | http://localhost:8008 |
| **OpenWebUI** | 🟢 運行中 | http://localhost:3333 |
| **Ollama** | 🟢 運行中 | http://localhost:11434 |

### 2. 知識圖譜內容

```
📊 節點統計:
- 1,135 件藝術作品 (Artwork)
- 894 位藝術家 (Artist)
- 175 個博物館 (Museum)
- 39 位作者 (Author)
- 30 個資源 (Resource)
- 8 個藝術時期 (Period)

🔗 關係統計:
- 1,302 個 CREATED 關係 (藝術家創作作品)
- 1,135 個 HOUSED_IN 關係 (作品收藏於博物館)
- 229 個 FROM_PERIOD 關係 (作品來自時期)
- 40 個 WROTE 關係 (作者撰寫資源)

總計: 2,281 個節點, 2,706 個關係
```

### 3. 可用的 Ollama 模型

```bash
✅ llama3-graph-rag:latest    4.9 GB  # 專門的 Graph RAG 模型
✅ llama3.1:8b                 4.9 GB  # 基礎模型
✅ gemma3:4b                   3.3 GB  # 輕量級模型
✅ bge-m3:latest               1.2 GB  # Embedding 模型
```

---

## 🎯 三種使用方式

### 方式一：直接使用 Ollama 命令行（最簡單）

```bash
# 使用專門的 Graph RAG 模型
ollama run llama3-graph-rag

# 範例對話：
# >>> Tell me about Renaissance art
# >>> What artworks by Vincent van Gogh are in the database?
# >>> Show me paintings in the Met Museum
```

**優點**:
- 最快速，立即可用
- 適合測試和快速查詢
- 模型已配置藝術史專業知識

**缺點**:
- 無法自動連接 Graph RAG API
- 需要手動指定查詢意圖

---

### 方式二：通過 Graph RAG API（程式化）

#### 查詢範例：

```bash
# 查詢梵谷作品
curl -X POST http://localhost:8008/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Tell me about Vincent van Gogh artworks",
    "strategy": "graph_only",
    "top_k": 5
  }'
```

#### 回應格式：

```json
{
  "answer": "基於知識圖譜的查詢結果...",
  "sources": [
    {
      "title": "Vincent van Gogh. Sunflowers",
      "artist": "Vincent van Gogh",
      "date": "1889",
      "period": "Impressionist",
      "score": 0.9
    }
  ],
  "strategy_used": "graph_only",
  "confidence_score": 0.95,
  "processing_time": 0.018
}
```

#### 常用查詢範例：

```bash
# 1. 查詢特定藝術家
curl -X POST http://localhost:8008/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Georges de La Tour paintings", "strategy": "graph_only"}'

# 2. 查詢藝術時期
curl -X POST http://localhost:8008/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Impressionist artworks", "strategy": "graph_only"}'

# 3. 查詢博物館館藏
curl -X POST http://localhost:8008/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Met Museum collection", "strategy": "graph_only"}'

# 4. 複雜關係查詢
curl -X POST http://localhost:8008/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me Renaissance painters and their works", "strategy": "graph_only", "top_k": 10}'
```

**優點**:
- 結構化的 JSON 回應
- 包含信心分數和來源
- 適合整合到應用程式
- 支援多種查詢策略

---

### 方式三：通過 OpenWebUI（最完整，推薦）

#### 步驟 1: 上傳 Function

1. 打開瀏覽器: http://localhost:3333
2. 登入 OpenWebUI
3. 點擊左側選單 → **Workspace** → **Functions**
4. 點擊 **+ Import Function**
5. 複製檔案內容並粘貼: `enhanced_openwebui_rag_function_v3.py`
6. 點擊 **Save**

#### 步驟 2: 使用 Graph RAG 模型

1. 在 OpenWebUI 中選擇模型: **llama3-graph-rag**
2. 確保 Function 已啟用（會顯示 🕸️ GraphRAG 圖示）
3. 開始對話！

#### 範例問題：

```
🎨 藝術家查詢：
- "Tell me about Renaissance artists"
- "Who is Vincent van Gogh?"
- "Show me French painters"

🖼️ 作品查詢：
- "What are some famous Impressionist paintings?"
- "Show me Van Gogh's Sunflowers"
- "Find paintings from the 1889"

🏛️ 博物館查詢：
- "What artworks are in the Met Museum?"
- "Show me European paintings"
- "Which museums have Baroque art?"

🕸️ 關係查詢：
- "How are Renaissance artists connected?"
- "Show me relationships between Impressionist painters"
- "What period does this artwork belong to?"
```

**優點**:
- 最佳用戶體驗
- 自動連接 Graph RAG API
- 視覺化對話介面
- 支援多輪對話
- 自動引用來源

---

## 🔍 驗證系統功能

### 檢查服務健康狀態

```bash
# 1. 檢查 Graph RAG API
curl http://localhost:8008/health
# 預期輸出: {"status":"healthy","neo4j":"connected"}

# 2. 檢查知識圖譜統計
curl http://localhost:8008/stats | python3 -m json.tool

# 3. 檢查 Neo4j 連接
docker exec art-history-neo4j cypher-shell -u neo4j -p arthistory123 "MATCH (n) RETURN count(n)"
# 預期輸出: 2281

# 4. 檢查 Ollama 模型
ollama list
# 應該看到 llama3-graph-rag

# 5. 測試 Graph RAG 查詢
curl -X POST http://localhost:8008/query \
  -H "Content-Type: application/json" \
  -d '{"query": "test query", "strategy": "graph_only"}'
```

---

## 📈 效能基準

基於實際測試結果：

| 查詢類型 | 處理時間 | 信心分數 | 結果數量 |
|---------|---------|----------|---------|
| **藝術家查詢** | ~0.02秒 | 0.95 | 5-10 |
| **作品查詢** | ~0.02秒 | 0.95 | 5-10 |
| **關係查詢** | ~0.03秒 | 0.75-0.95 | 3-8 |
| **複雜查詢** | ~0.05秒 | 0.75 | 10+ |

**系統配置**:
- GPU: RTX 4090 24GB
- Neo4j: 2,281 nodes, 2,706 relationships
- LLM: llama3.1:8b (4.9GB)

---

## 🛠️ 常用操作

### 重啟 Graph RAG 服務

```bash
# 停止現有服務
ps aux | grep neo4j_graph_rag_server
kill <PID>

# 重新啟動
cd /mnt/c/Users/ssking1999/Desktop/藝術史資料庫/art-history-database
./langchain-env/bin/python3 neo4j_graph_rag_server.py > graph_rag_server.log 2>&1 &

# 檢查日誌
tail -f graph_rag_server.log
```

### 查看 Neo4j 資料

```bash
# 在終端使用 cypher-shell
docker exec -it art-history-neo4j cypher-shell -u neo4j -p arthistory123

# 或通過瀏覽器
# 訪問: http://localhost:7474
# 帳號: neo4j / arthistory123
```

### 常用 Cypher 查詢

```cypher
// 查看所有節點類型和數量
MATCH (n) RETURN labels(n)[0] as type, count(n) as count ORDER BY count DESC;

// 查看所有關係類型
MATCH ()-[r]->() RETURN type(r) as type, count(r) as count ORDER BY count DESC;

// 查詢特定藝術家
MATCH (artist:Artist {name: "Vincent van Gogh"})-[:CREATED]->(artwork:Artwork)
RETURN artist, artwork LIMIT 10;

// 查詢特定時期的作品
MATCH (period:Period {name: "Renaissance"})<-[:FROM_PERIOD]-(artwork:Artwork)
RETURN period, artwork LIMIT 10;

// 查詢博物館館藏
MATCH (museum:Museum {name: "Met Museum - European Paintings"})<-[:HOUSED_IN]-(artwork:Artwork)
RETURN museum, artwork LIMIT 10;
```

---

## 🐛 常見問題

### Q1: Graph RAG API 無回應

```bash
# 檢查服務是否運行
ps aux | grep neo4j_graph_rag_server

# 檢查端口是否被佔用
lsof -i :8008

# 查看錯誤日誌
tail -n 50 graph_rag_server.log
```

### Q2: Neo4j 連接失敗

```bash
# 檢查 Docker 容器
docker ps | grep neo4j

# 重啟 Neo4j
docker restart art-history-neo4j

# 測試連接
docker exec art-history-neo4j cypher-shell -u neo4j -p arthistory123 "RETURN 1"
```

### Q3: Ollama 模型無法使用

```bash
# 檢查 Ollama 服務
ollama list

# 重新創建模型
ollama create llama3-graph-rag -f /tmp/llama3-graph-rag.modelfile

# 測試模型
ollama run llama3-graph-rag "test"
```

### Q4: 查詢結果為空

可能原因：
1. **關鍵詞不匹配**: 嘗試使用更具體的名稱
2. **資料庫為空**: 確認 Neo4j 有資料 (`curl http://localhost:8008/stats`)
3. **拼寫錯誤**: 檢查藝術家/作品名稱拼寫

解決方案：
```bash
# 檢查資料庫內容
docker exec art-history-neo4j cypher-shell -u neo4j -p arthistory123 \
  "MATCH (n:Artist) RETURN n.name LIMIT 20"

# 使用更通用的查詢
curl -X POST http://localhost:8008/query \
  -H "Content-Type: application/json" \
  -d '{"query": "paintings", "strategy": "graph_only", "top_k": 10}'
```

---

## 📚 進階使用

### 自定義 Graph RAG 模型

```bash
# 創建專門針對特定領域的模型
cat > /tmp/custom-model.modelfile << 'EOF'
FROM llama3.1:8b

SYSTEM """你是專注於印象派藝術的專家...
"""

PARAMETER temperature 0.2
PARAMETER top_p 0.95
EOF

ollama create custom-art-expert -f /tmp/custom-model.modelfile
```

### Python 程式化查詢

```python
import requests

def query_graph_rag(question: str, top_k: int = 5):
    response = requests.post(
        "http://localhost:8008/query",
        json={
            "query": question,
            "strategy": "graph_only",
            "top_k": top_k
        }
    )
    return response.json()

# 使用範例
result = query_graph_rag("Tell me about Vincent van Gogh")
print(f"Answer: {result['answer']}")
print(f"Confidence: {result['confidence_score']}")
print(f"Sources: {len(result['sources'])}")
```

---

## 🎉 總結

你現在擁有一個完整的 Graph RAG 系統：

✅ **知識圖譜**: 2,281 個藝術史實體
✅ **Graph RAG API**: 高效的關係查詢
✅ **專門 LLM**: 藝術史專家模型
✅ **Web 介面**: OpenWebUI 整合

### 推薦工作流程：

1. **日常使用**: OpenWebUI + llama3-graph-rag 模型
2. **快速測試**: 命令行 `ollama run llama3-graph-rag`
3. **程式整合**: 直接調用 Graph RAG API

### 下一步建議：

1. 🎨 **探索資料**: 在 Neo4j Browser 可視化知識圖譜
2. 📊 **增加資料**: 下載更多藝術史資料
3. 🔧 **優化查詢**: 調整 top_k 參數和查詢策略
4. 🤖 **實驗模型**: 嘗試不同的 Ollama 模型配置

---

**文檔更新**: 2025-10-15
**系統版本**: Graph RAG v1.0.0
**支援**: 查看 `GRAPH_RAG_SETUP_GUIDE.md` 獲取詳細說明

🎨 祝你使用愉快！
