# 🕸️ Neo4j Graph RAG 整合完成指南

## ✅ 已完成的工作

### 1. Neo4j 知識圖譜
- **狀態**: ✅ 已導入完成
- **內容**:
  - 1,135 件藝術作品
  - 894 位藝術家
  - 175 個博物館
  - 8 個藝術時期
  - 2,706 個關係

### 2. Graph RAG 服務器
- **狀態**: ✅ 已啟動運行
- **地址**: http://localhost:8008
- **功能**:
  - 基於 Neo4j 的知識圖譜檢索
  - 實體關係分析
  - 時期和風格關聯查詢
  - RESTful API 接口

### 3. 測試結果
```bash
# 健康檢查
curl http://localhost:8008/health
# 輸出: {"status":"healthy","neo4j":"connected"}

# 知識圖譜統計
curl http://localhost:8008/stats

# 測試查詢（Renaissance 藝術）
curl -X POST http://localhost:8008/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Tell me about Renaissance art", "strategy": "graph_only"}'
```

---

## 🚀 快速使用 Graph RAG

### 方式一：通過 OpenWebUI（推薦）

#### 步驟 1: 上傳 Function

1. 打開 OpenWebUI: http://localhost:3333
2. 點擊左側選單 → **Workspace** → **Functions**
3. 點擊 **+ Import Function**
4. 複製並粘貼 `enhanced_openwebui_rag_function_v3.py` 的內容
5. 點擊 **Save**

#### 步驟 2: 創建 Graph RAG 模型

在終端執行：

```bash
cd art-history-database

# 創建簡單的 Graph RAG 模型（基於 llama3.1）
ollama create llama3-graph-rag -f - <<EOF
FROM llama3.1:8b

SYSTEM """你是專業的藝術史學者，使用 Neo4j 知識圖譜進行查詢。

當前策略: GraphRAG (graph_only)
專長: 實體關係分析、時期脈絡、藝術家和作品連結

請根據知識圖譜的結構化資料，專業地回答藝術史問題。
特別強調實體間的關係、時間序列和影響傳承。
"""

PARAMETER temperature 0.1
PARAMETER top_p 0.9
EOF
```

#### 步驟 3: 在 OpenWebUI 中使用

1. 在 OpenWebUI 中選擇模型 `llama3-graph-rag`
2. 確保 Function 已啟用
3. 開始提問！

**範例問題**：
- "Tell me about Renaissance artists"
- "What artworks are in the Met Museum?"
- "Show me relationships between Baroque artists"
- "What are the characteristics of Impressionist art?"

---

### 方式二：直接通過 API 使用

```bash
# 查詢文藝復興藝術
curl -X POST http://localhost:8008/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Tell me about Renaissance art",
    "strategy": "graph_only",
    "top_k": 5
  }' | python3 -m json.tool

# 查詢特定藝術家
curl -X POST http://localhost:8008/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Vincent van Gogh artworks",
    "strategy": "graph_only",
    "top_k": 10
  }' | python3 -m json.tool

# 查詢博物館館藏
curl -X POST http://localhost:8008/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Met Museum collection",
    "strategy": "graph_only",
    "top_k": 10
  }' | python3 -m json.tool
```

---

## 📊 Graph RAG 服務器管理

### 啟動服務器

```bash
cd art-history-database
./langchain-env/bin/python3 neo4j_graph_rag_server.py > graph_rag_server.log 2>&1 &
```

### 檢查狀態

```bash
# 檢查服務器健康狀態
curl http://localhost:8008/health

# 查看知識圖譜統計
curl http://localhost:8008/stats | python3 -m json.tool

# 查看可用策略
curl http://localhost:8008/system/strategies | python3 -m json.tool

# 查看日誌
tail -f graph_rag_server.log
```

### 停止服務器

```bash
# 找到進程 ID
ps aux | grep neo4j_graph_rag_server

# 停止進程（替換 PID）
kill <PID>
```

---

## 🔍 Graph RAG 功能特色

### 1. 實體關係查詢
- 查詢藝術家與作品的關係
- 探索作品與博物館的收藏關係
- 分析藝術時期與作品的關聯

### 2. 結構化搜索
- 按藝術家名稱搜索
- 按作品標題搜索
- 按藝術時期篩選
- 按博物館館藏查詢

### 3. 關係圖譜
- CREATED：藝術家創作作品
- HOUSED_IN：作品收藏於博物館
- FROM_PERIOD：作品來自時期
- WROTE：作者撰寫書籍

### 4. 智能查詢
- 自動提取查詢關鍵詞
- 多維度實體搜索
- 結果相關度排序
- 信心分數評估

---

## 🎯 使用範例

### 範例 1：查詢藝術家作品

```bash
curl -X POST http://localhost:8008/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Georges de La Tour paintings",
    "strategy": "graph_only"
  }'
```

**預期輸出**：
- 藝術家資訊（國籍、年代）
- 相關作品列表
- 作品收藏博物館
- 藝術時期關聯

### 範例 2：時期分析

```bash
curl -X POST http://localhost:8008/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Baroque period artworks",
    "strategy": "graph_only"
  }'
```

**預期輸出**：
- 巴洛克時期作品列表
- 該時期的代表藝術家
- 作品的博物館分布
- 時期特徵分析

### 範例 3：博物館館藏

```bash
curl -X POST http://localhost:8008/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Met Museum European Paintings",
    "strategy": "graph_only"
  }'
```

**預期輸出**：
- 博物館館藏作品
- 作品的藝術家
- 作品的年代和風格
- 館藏特色分析

---

## 🛠️ 進階配置

### 修改查詢參數

編輯 `neo4j_graph_rag_server.py`：

```python
# 調整搜索結果數量
def search_artworks(self, keywords: List[str], limit: int = 10):  # 改為 10

# 調整信心分數計算
def calculate_confidence(self, results: Dict) -> float:
    total_results = sum(len(v) for v in results.values())
    if total_results >= 20:  # 提高門檻
        return 0.95
```

### 添加新的查詢類型

在 `Neo4jGraphRAG` 類中添加新方法：

```python
def search_by_style(self, style: str, limit: int = 5) -> List[Dict]:
    """按藝術風格搜索"""
    with self.driver.session() as session:
        query = """
        MATCH (artwork:Artwork)
        WHERE artwork.style CONTAINS $style
        RETURN artwork.title, artwork.artist, artwork.date
        LIMIT $limit
        """
        result = session.run(query, style=style, limit=limit)
        return [dict(record) for record in result]
```

---

## 📈 效能優化

### 1. Neo4j 索引

在 Neo4j Browser (http://localhost:7474) 執行：

```cypher
// 為藝術家名稱創建索引
CREATE INDEX artist_name_index FOR (a:Artist) ON (a.name);

// 為作品標題創建索引
CREATE INDEX artwork_title_index FOR (a:Artwork) ON (a.title);

// 為時期名稱創建索引
CREATE INDEX period_name_index FOR (p:Period) ON (p.name);
```

### 2. 查詢優化

```python
# 使用參數化查詢
session.run("MATCH (n:Artist {name: $name}) RETURN n", name=artist_name)

# 限制返回結果
RETURN artwork LIMIT 10

# 使用 OPTIONAL MATCH 避免空結果
OPTIONAL MATCH (artist)-[:CREATED]->(artwork)
```

---

## 🐛 常見問題

### Q1: 服務器啟動失敗
```bash
# 檢查 Neo4j 是否運行
docker ps | grep neo4j

# 檢查端口是否被占用
lsof -i :8008

# 查看錯誤日誌
cat graph_rag_server.log
```

### Q2: 查詢無結果
```bash
# 檢查 Neo4j 數據
docker exec art-history-neo4j cypher-shell -u neo4j -p arthistory123 \
  "MATCH (n) RETURN count(n)"

# 檢查關鍵詞提取
# 在查詢日誌中查看提取的關鍵詞
tail -f graph_rag_server.log | grep "提取的關鍵詞"
```

### Q3: OpenWebUI Function 不工作
1. 確保 Graph RAG 服務器在運行
2. 檢查 Function 中的 API URL 是否正確
3. 查看 OpenWebUI 日誌錯誤訊息

---

## 📚 相關文檔

- **Neo4j 使用指南**: `Neo4j使用指南.md`
- **RAG 框架使用手冊**: `RAG框架使用手冊.md`
- **系統環境檢查報告**: `系統環境檢查報告.md`
- **Docker 服務管理**: `Docker服務管理指南.md`

---

## 🎉 總結

您的 Neo4j Graph RAG 系統已經完全整合並運行！

**當前狀態**：
- ✅ Neo4j 知識圖譜：2,281 個節點，2,706 個關係
- ✅ Graph RAG 服務器：運行在 http://localhost:8008
- ✅ OpenWebUI：運行在 http://localhost:3333
- ✅ Ollama 模型：llama3.1:8b, gemma3:4b, bge-m3

**下一步**：
1. 在 OpenWebUI 中上傳 Function
2. 創建 Graph RAG 模型
3. 開始使用 Graph RAG 查詢藝術史知識！

祝您使用愉快！🎨
