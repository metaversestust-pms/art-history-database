# 藝術史資料擴增與RAG整合指南

本指南說明如何使用新建立的腳本系統來擴增藝術史資料庫，並整合到多種RAG策略中使用。

## 📋 目錄

1. [系統概述](#系統概述)
2. [前置需求](#前置需求)
3. [快速開始](#快速開始)
4. [詳細步驟](#詳細步驟)
5. [腳本說明](#腳本說明)
6. [故障排除](#故障排除)

---

## 系統概述

本系統整合了以下組件：

### 🤖 爬蟲系統
- **renaissance-baroque-crawler.js** - 文藝復興與巴洛克時期專門爬蟲
- **specialized-art-crawler.js** - 專門藝術主題爬蟲（亞洲藝術、當代藝術、建築等）
- **harvard-art-museums-crawler.js** - 哈佛藝術博物館API爬蟲
- **europeana-crawler.js** - Europeana文化遺產平台爬蟲

### 🗄️ 資料庫系統
- **ChromaDB** (port 8001) - 向量資料庫，用於語義檢索
- **Neo4j** (port 7687) - 圖譜資料庫，用於知識圖譜和關係推理
- **PostgreSQL** (port 5432) - 關係型資料庫（可選）

### 🧠 RAG策略
1. **Vector Only RAG** 🔍 - 純向量語義檢索
2. **Graph Only RAG** 🕸️ - 知識圖譜檢索
3. **Hybrid Balanced RAG** ⚖️ - 向量+圖譜混合
4. **Advanced RAG** 🎯 - 多級檢索重排
5. **Agentic RAG** 🤖 - 智能代理推理
6. **Self RAG** 🔄 - 自我反思迭代
7. **Naive RAG** 📝 - 基礎檢索生成

### 🤖 LLM模型
- Llama 3.1 8B 🦙
- Qwen 3 8B 🔮
- Gemma 3 4B 💎
- DeepSeek-R1 8B 🧠
- GPT-OSS 20B 🤖
- Llama 3 Graph RAG 🕸️

**總計：42種 RAG+LLM 組合**

---

## 前置需求

### 必需服務

確保以下服務正在運行：

```bash
# 檢查 Neo4j
curl http://localhost:7474

# 檢查 ChromaDB
curl http://localhost:8001/api/v1/heartbeat

# 檢查 Ollama
curl http://localhost:11434/api/tags

# 檢查 RAG 管理器
curl http://localhost:8007/health
```

### 必需軟體

- **Node.js** >= 16.0.0
- **Python** >= 3.8
- **Docker** 和 **Docker Compose** (用於服務)

### Python 依賴

```bash
cd art-history-database/langchain-rag
pip install -r requirements.txt
```

主要依賴包括：
- chromadb
- neo4j
- requests
- fastapi
- uvicorn

---

## 快速開始

### 方法 1: 使用完整流水線（推薦）

一鍵執行所有步驟：

```bash
cd art-history-database
bash run-data-expansion-pipeline.sh
```

這將自動執行：
1. ✅ 環境檢查
2. 🤖 執行所有爬蟲收集資料
3. 🔄 向量化並整合到資料庫
4. 🧪 測試RAG系統整合

### 方法 2: 分步執行

如果需要更精細的控制，可以分步執行：

```bash
# 步驟 1: 收集藝術史資料
node expand-art-history-data.js

# 步驟 2: 向量化並整合
python3 integrate-to-vector-db.py --hours 24

# 步驟 3: 測試RAG整合
node test-rag-with-new-data.js
```

---

## 詳細步驟

### 步驟 1: 資料收集

**腳本**: `expand-art-history-data.js`

此腳本會依序執行所有配置的爬蟲：

```bash
node expand-art-history-data.js
```

**輸出**:
- 原始資料保存在: `data/raw/`
- 摘要報告: `data-expansion-summary.json`

**預期結果**:
```
🚀 開始藝術史資料收集任務
═══════════════════════════════════════
⏳ 啟動爬蟲: 文藝復興與巴洛克時期爬蟲
✅ 文藝復興與巴洛克時期爬蟲 完成 (120.5秒)
...
📊 總藝術品數量: 850
```

**收集的資料類型**:
- 文藝復興時期藝術品 (~200件)
- 巴洛克時期藝術品 (~150件)
- 專門藝術主題 (~300件)
- 哈佛博物館藏品 (~100件)
- Europeana 資料 (~100件)

---

### 步驟 2: 向量化與整合

**腳本**: `integrate-to-vector-db.py`

此腳本會：
1. 讀取最近收集的資料文件
2. 標準化資料格式
3. 使用 Ollama 生成向量嵌入
4. 批量導入 ChromaDB
5. 建立 Neo4j 圖譜節點和關係

```bash
# 處理最近24小時的資料
python3 integrate-to-vector-db.py --hours 24

# 處理最近7天的資料
python3 integrate-to-vector-db.py --hours 168
```

**資料流程**:
```
原始JSON資料
  → 標準化格式
  → 文本表示
  → 向量嵌入
  → ChromaDB + Neo4j
```

**ChromaDB 資料結構**:
```json
{
  "id": "met_12345",
  "document": "Title: Mona Lisa\nArtist: Leonardo da Vinci\n...",
  "metadata": {
    "title": "Mona Lisa",
    "artist": "Leonardo da Vinci",
    "date": "1503-1519",
    "source": "met_museum"
  },
  "embedding": [0.123, -0.456, ...]
}
```

**Neo4j 圖譜結構**:
```cypher
(Artist {name: "Leonardo da Vinci"})
  -[:CREATED]->
(Artwork {title: "Mona Lisa", date: "1503-1519"})
  -[:BELONGS_TO_PERIOD]->
(Period {name: "Renaissance"})
```

**預期輸出**:
```
🔌 連接服務...
✅ ChromaDB 連接成功
✅ Neo4j 連接成功
✅ Ollama 連接成功
📂 處理文件: renaissance_baroque_2025-10-18.json
  提取了 250 個藝術品
✅ 成功向量化 250 個藝術品
✅ 成功添加 250 個藝術品到Neo4j
...
📊 向量資料庫整合摘要
處理文件: 4/4
總藝術品數: 850
向量化項目: 850
Neo4j項目: 850
```

---

### 步驟 3: RAG整合測試

**腳本**: `test-rag-with-new-data.js`

此腳本會測試新資料是否成功整合到不同的RAG策略中：

```bash
node test-rag-with-new-data.js
```

**測試查詢**:
1. "文藝復興時期的藝術特點" - 測試向量/圖譜/混合策略
2. "Leonardo da Vinci的作品" - 測試實體檢索
3. "巴洛克時期和文藝復興時期的差異" - 測試關係推理
4. "亞洲藝術的特色" - 測試新收集的專門主題

**成功標準**:
- ✅ 回答長度 > 50 字符
- ✅ 有來源文檔 (> 0個)
- ✅ 包含預期關鍵詞
- ✅ 響應時間 < 60秒

**預期輸出**:
```
🧪 RAG 系統新資料整合測試
═══════════════════════════════════════
📋 狀態: healthy
  - Neo4j: ✅
  - ChromaDB: ✅
  - Ollama: ✅

測試查詢: "文藝復興時期的藝術特點"
  策略: vector_only
  回答長度: 345 字符
  來源數量: 5
  響應時間: 2341ms
  關鍵詞匹配: ✅
✅ 測試通過
...

📊 測試摘要
總測試數: 12
通過: 11
失敗: 1
成功率: 91.7%

策略表現:
  vector_only: 4/4 (100%)
  graph_only: 3/4 (75%)
  hybrid_balanced: 2/2 (100%)
  agentic_rag: 2/2 (100%)

平均響應時間: 3125ms
```

---

## 腳本說明

### expand-art-history-data.js

**功能**: 整合執行多個爬蟲，收集藝術史資料

**特點**:
- 自動檢測爬蟲文件
- 順序執行，避免API過載
- 爬蟲間自動延遲
- 統計收集結果
- 生成摘要報告

**配置**:
修改腳本中的 `crawlers` 陣列來添加或移除爬蟲：

```javascript
const crawlers = [
    {
        path: './my-custom-crawler.js',
        name: '自定義爬蟲'
    },
    // ...
];
```

---

### integrate-to-vector-db.py

**功能**: 向量化資料並整合到 ChromaDB 和 Neo4j

**參數**:
- `--hours N` - 處理最近N小時的資料文件（預設：24）

**環境變數**:
```bash
export CHROMADB_HOST=localhost
export CHROMADB_PORT=8001
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=arthistory123
export OLLAMA_BASE_URL=http://localhost:11434
```

**資料標準化**:
腳本支援多種來源格式：
- Met Museum API 格式
- Europeana API 格式
- 通用 JSON 格式

自動提取的字段：
- id, title, artist, date, description
- medium, culture, period, source
- metadata (完整原始資料)

---

### test-rag-with-new-data.js

**功能**: 測試 RAG 系統對新資料的整合效果

**配置**:
修改 `testQueries` 陣列來自定義測試查詢：

```javascript
{
    query: '你的測試查詢',
    expectedKeywords: ['關鍵詞1', '關鍵詞2'],
    strategies: ['vector_only', 'graph_only']
}
```

**環境變數**:
```bash
export RAG_MANAGER_URL=http://localhost:8007
```

---

### run-data-expansion-pipeline.sh

**功能**: 一鍵執行完整的資料擴增流水線

**執行流程**:
1. 環境檢查（檢查命令和服務）
2. 執行爬蟲收集資料
3. 向量化並整合資料
4. 測試 RAG 系統整合

**日誌顏色**:
- 🔵 藍色 - 資訊
- 🟢 綠色 - 成功
- 🟡 黃色 - 警告
- 🔴 紅色 - 錯誤

---

## 故障排除

### 問題 1: ChromaDB 連接失敗

**症狀**:
```
❌ ChromaDB 連接失敗: Connection refused
```

**解決方案**:
```bash
# 檢查 ChromaDB 是否運行
curl http://localhost:8001/api/v1/heartbeat

# 如果未運行，啟動 ChromaDB
cd art-history-database
docker-compose up -d chromadb

# 或使用獨立安裝
chroma run --host 0.0.0.0 --port 8001
```

---

### 問題 2: Neo4j 連接失敗

**症狀**:
```
❌ Neo4j 連接失敗: Authentication failed
```

**解決方案**:
```bash
# 檢查密碼是否正確
export NEO4J_PASSWORD=你的密碼

# 重置 Neo4j 密碼
docker-compose exec neo4j cypher-shell -u neo4j -p oldpassword
# 在 cypher-shell 中執行:
ALTER USER neo4j SET PASSWORD 'newpassword';
```

---

### 問題 3: Ollama 模型未找到

**症狀**:
```
❌ 向量生成失敗: model not found
```

**解決方案**:
```bash
# 拉取嵌入模型
ollama pull nomic-embed-text

# 拉取 LLM 模型
ollama pull llama3.1:8b
ollama pull qwen3:8b
ollama pull gemma3:4b
ollama pull deepseek-r1:8b

# 檢查已安裝的模型
ollama list
```

---

### 問題 4: 爬蟲 API 金鑰錯誤

**症狀**:
```
❌ 搜尋失敗: 401 Unauthorized
```

**解決方案**:
檢查 `.env` 文件中的 API 金鑰：

```bash
# Europeana API Key
EUROPEANA_API_KEY=your_api_key

# Harvard Art Museums API Key
HARVARD_API_KEY=your_api_key
```

申請 API 金鑰：
- Europeana: https://pro.europeana.eu/page/get-api
- Harvard Art Museums: https://docs.google.com/forms/d/e/1FAIpQLSfkmEBqH76HLMMiCC-GPPnhcvHC9aJS86E32dOd0Z8MpY2rvQ/viewform

---

### 問題 5: 記憶體不足

**症狀**:
```
FATAL ERROR: Reached heap limit
```

**解決方案**:
```bash
# 增加 Node.js 記憶體限制
export NODE_OPTIONS="--max-old-space-size=4096"

# 或在執行時指定
node --max-old-space-size=4096 expand-art-history-data.js

# 批量處理 - 減小批次大小
# 在 integrate-to-vector-db.py 中:
batch_size = 50  # 預設 100，降低到 50
```

---

### 問題 6: RAG 測試失敗

**症狀**:
```
❌ 測試失敗：回答不完整或缺少關鍵資訊
```

**診斷步驟**:

1. **檢查資料是否成功導入**:
```bash
# ChromaDB 文檔數量
curl http://localhost:8001/api/v1/collections/art_history

# Neo4j 節點數量
cypher-shell "MATCH (n) RETURN labels(n), count(*)"
```

2. **手動測試查詢**:
```bash
curl -X POST http://localhost:8007/api/v1/query \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "Leonardo da Vinci",
    "model_combination_id": "llama3.1:8b@vector_only",
    "max_results": 5
  }'
```

3. **檢查 RAG 管理器日誌**:
```bash
# 如果使用 Docker
docker-compose logs rag-manager

# 或查看應用日誌
tail -f langchain-rag/rag_manager.log
```

---

## 高級配置

### 自定義爬蟲

創建新的爬蟲文件 `my-crawler.js`:

```javascript
class MyCrawler {
    async run() {
        // 1. 獲取資料
        const data = await this.fetchData();

        // 2. 處理資料
        const processed = this.processData(data);

        // 3. 保存到 data/raw/
        const filename = `my_data_${Date.now()}.json`;
        fs.writeFileSync(
            `data/raw/${filename}`,
            JSON.stringify(processed, null, 2)
        );
    }
}
```

### 自定義資料格式

在 `integrate-to-vector-db.py` 中添加新的格式處理：

```python
def normalize_artwork_data(self, item: Dict[str, Any], source: str):
    # 添加自定義格式支援
    if source == 'my_custom_source':
        normalized = {
            'id': item['custom_id'],
            'title': item['custom_title'],
            # ...
        }
    # ...
```

### 自定義測試查詢

在 `test-rag-with-new-data.js` 中添加：

```javascript
{
    query: '你的自定義查詢',
    expectedKeywords: ['關鍵詞'],
    strategies: ['vector_only', 'graph_only', 'hybrid_balanced']
}
```

---

## 效能優化

### 1. 批次大小優化

```python
# integrate-to-vector-db.py
batch_size = 100  # 根據可用記憶體調整
```

### 2. 並行處理

```bash
# 並行執行多個爬蟲
node renaissance-baroque-crawler.js &
node specialized-art-crawler.js &
wait
```

### 3. 快取查詢

RAG 管理器已內建查詢快取，無需額外配置。

檢查快取統計：
```bash
curl http://localhost:8007/api/v1/cache/stats
```

清空快取：
```bash
curl -X POST http://localhost:8007/api/v1/cache/clear
```

---

## 監控與維護

### 資料庫大小監控

```bash
# ChromaDB 文檔數
curl http://localhost:8001/api/v1/collections/art_history | jq '.document_count'

# Neo4j 節點和關係數
cypher-shell "MATCH (n) RETURN count(n) as nodes"
cypher-shell "MATCH ()-[r]->() RETURN count(r) as relationships"
```

### 定期資料更新

建議設定 cron 任務定期更新資料：

```bash
# 每週日凌晨2點執行資料更新
0 2 * * 0 cd /path/to/art-history-database && bash run-data-expansion-pipeline.sh
```

### 備份策略

```bash
# 備份 ChromaDB
docker-compose exec chromadb chromadb utils export --path /backup

# 備份 Neo4j
docker-compose exec neo4j neo4j-admin dump --to=/backup/neo4j-backup.dump

# 備份原始資料
tar -czf data-raw-backup-$(date +%Y%m%d).tar.gz data/raw/
```

---

## 總結

恭喜！您現在已經掌握了藝術史資料擴增與RAG整合系統的完整使用方法。

**關鍵要點**:
1. ✅ 使用 `run-data-expansion-pipeline.sh` 一鍵執行完整流程
2. ✅ 支援 42 種 RAG+LLM 組合
3. ✅ 自動向量化並整合到 ChromaDB 和 Neo4j
4. ✅ 內建測試和驗證機制

**下一步**:
- 探索不同 RAG 策略的效能差異
- 添加更多藝術史資料來源
- 優化查詢和檢索效能
- 整合到生產環境

**參考資源**:
- RAG 策略詳解: `RAG_METHODS_OVERVIEW.md`
- API 文件: `API_DOCUMENTATION.md`
- Docker 部署: `DEPLOYMENT_GUIDE.md`

如有問題，請查看 [故障排除](#故障排除) 章節或查閱相關日誌文件。
