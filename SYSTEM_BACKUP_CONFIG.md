# 藝術史資料庫系統配置備份

**備份時間**: 2025-12-06
**系統位置**: `/mnt/c/Users/ssking1999/Desktop/藝術史資料庫/art-history-database`
**WSL環境**: Ubuntu on Windows (WSL2)

---

## 📋 目錄

1. [Docker 容器狀態](#docker-容器狀態)
2. [關鍵環境配置](#關鍵環境配置)
3. [資料庫配置](#資料庫配置)
4. [最近修復記錄](#最近修復記錄)
5. [重要文檔索引](#重要文檔索引)
6. [快速恢復步驟](#快速恢復步驟)

---

## 1. Docker 容器狀態

### 運行中的容器

```
容器名稱                        映像檔                                              狀態                     端口映射
art-history-openwebui        ghcr.io/open-webui/open-webui:main                Up 16 hours (healthy)    0.0.0.0:8080->8080/tcp
art-history-chromadb         chromadb/chroma:latest                            Up 3 weeks               0.0.0.0:8000->8000/tcp
art-history-neo4j            neo4j:5.16.0                                      Up 3 weeks (healthy)     0.0.0.0:7474->7474/tcp, 0.0.0.0:7687->7687/tcp
art-database-nginx           nginx:alpine                                      Up 3 weeks               0.0.0.0:80->80/tcp
art-history-rag-manager-v2   art-history-database-rag-manager-v2               Up 3 weeks (unhealthy)   0.0.0.0:8007->8007/tcp
art-history-ollama           ollama/ollama:latest                              Up 2 weeks (unhealthy)   0.0.0.0:11434->11434/tcp
art-database-postgres        postgres:15-alpine                                Up 7 weeks (healthy)     0.0.0.0:5432->5432/tcp
art-database-redis           redis:7-alpine                                    Up 7 weeks (healthy)     0.0.0.0:6379->6379/tcp
art-database-elasticsearch   docker.elastic.co/elasticsearch/elasticsearch:8.8.0   Up 7 weeks (healthy)     0.0.0.0:9200->9200/tcp
```

### Docker 網路

```
- art-history-database_art-network (bridge)
- art-history-network (bridge)
```

### Docker 資料卷

```
- art-history-database_chroma_data
- art-history-database_chromadb_data
- art-history-database_es_data
- art-history-database_neo4j_data
- art-history-database_neo4j_import
- art-history-database_neo4j_logs
- art-history-database_neo4j_plugins
- art-history-database_ollama_data
- art-history-database_openwebui_data
- art-history-database_postgres_data
- art-history-database_rag-manager-data
- art-history-database_redis_data
```

---

## 2. 關鍵環境配置

### OpenWebUI 環境變數

```bash
# 資料庫連接
VECTOR_DB=chroma
CHROMA_HTTP_HOST=art-history-chromadb
CHROMA_HTTP_PORT=8000

# Ollama 連接
OLLAMA_BASE_URL=http://art-history-ollama:11434
OLLAMA_API_BASE_URL=http://art-history-ollama:11434

# RAG 配置
ENABLE_RAG_LOCAL=true
RAG_EMBEDDING_ENGINE=ollama
RAG_EMBEDDING_MODEL=nomic-embed-text:latest
RAG_TOP_K=5
RAG_API_BASE_URL=http://host.docker.internal:8007

# 分塊設定
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# OpenAI API (用於 RAG 整合)
OPENAI_API_BASE_URLS=http://art-history-openwebui-integration:8009/v1
OPENAI_API_KEYS=sk-art-history-rag

# 安全與認證
WEBUI_AUTH=false
ENABLE_SIGNUP=true
DEFAULT_USER_ROLE=user

# 功能開關
ENABLE_IMAGE_GENERATION=false
ENABLE_MESSAGE_RATING=true
ENABLE_RAG_WEB_SEARCH=true
ENABLE_COMMUNITY_SHARING=false

# 日誌
WEBUI_LOG_LEVEL=INFO

# 隱私
SCARF_NO_ANALYTICS=true
DO_NOT_TRACK=true
ANONYMIZED_TELEMETRY=false
```

### Docker Compose 文件

**主要配置**: `docker-compose.yml`
**其他配置**:
- `docker-compose.openwebui.yml` - OpenWebUI 專用
- `docker-compose.neo4j.yml` - Neo4j 圖資料庫
- `docker-compose.rag-manager.yml` - RAG 管理器
- `docker-compose.complete.yml` - 完整系統配置

---

## 3. 資料庫配置

### Neo4j

```
端口: 7474 (HTTP), 7687 (Bolt)
版本: 5.16.0
狀態: Healthy
密碼: 存儲於 .env 文件
```

**訪問**: http://localhost:7474

### ChromaDB

```
端口: 8000
版本: latest
狀態: Running
Collection: art_history_collection
```

**訪問**: http://localhost:8000

### PostgreSQL

```
端口: 5432
版本: 15-alpine
資料庫: art_history_db
用戶: art_user
狀態: Healthy
```

### Redis

```
端口: 6379
版本: 7-alpine
狀態: Healthy
```

### Elasticsearch

```
端口: 9200
版本: 8.8.0
狀態: Healthy
```

---

## 4. 最近修復記錄

### ✅ OpenWebUI 上傳問題修復 (2025-12-05)

**問題**: 使用 OpenWebUI Knowledge Base 上傳文件時出現 `400: list index out of range` 錯誤

**根本原因**:
- OpenWebUI 使用 OpenAI 格式的 `{"input": [texts]}` 參數
- Ollama API 只支援 `{"prompt": "text"}` 格式
- 導致 Ollama 返回空嵌入陣列 `[]`

**修復方案**:
- 修改文件: `/app/backend/open_webui/retrieval/utils.py` (容器內)
- 函數: `generate_ollama_batch_embeddings`
- 改為逐一處理文本，使用正確的 Ollama API 格式

**修復腳本**: `fix_ollama_batch_embeddings.sh`
**測試腳本**: `test_openwebui_upload_fix.py`
**備份位置**: `/app/backend/open_webui/retrieval/utils.py.backup_20251205_184218`

**驗證結果**:
```
✅ 測試通過！
   輸入文本數: 3
   生成嵌入數: 3 (修復前為 0)
   嵌入維度: 768
```

**相關文檔**:
- `OpenWebUI上傳問題最終解決方案.md`
- `OpenWebUI批次嵌入修復報告.md`
- `OpenWebUI資料整合問題診斷報告.md`

### 修復歷程總結

#### 第一階段: ChromaDB 連接問題
- **問題**: "Could not connect to ChromaDB"
- **原因**: 端口配置錯誤 (8001 vs 8000)
- **解決**: 使用 `--chromadb-port 8000`
- **文檔**: `ChromaDB問題修復報告.md`

#### 第二階段: OpenWebUI 不使用上傳資料
- **問題**: OpenWebUI 回答錯誤
- **原因**: CLI 匯入繞過了 OpenWebUI 的追蹤系統
- **發現**: 必須通過 Web 介面上傳
- **文檔**: `OpenWebUI資料整合問題診斷報告.md`

#### 第三階段: 上傳錯誤修復
- **問題**: "400: list index out of range"
- **原因**: API 參數格式不匹配
- **解決**: 改用 Ollama 原生格式
- **文檔**: `OpenWebUI批次嵌入修復報告.md`

---

## 5. 重要文檔索引

### 系統部署與配置

- `DEPLOYMENT_GUIDE.md` - 完整部署指南
- `OPENWEBUI_SETUP_GUIDE.md` - OpenWebUI 設置指南
- `DOCKER-COMPOSE-SETUP.md` - Docker Compose 配置
- `OLLAMA_SETUP_GUIDE.md` - Ollama 本地 LLM 設置

### RAG 系統

- `RAG_METHODS_OVERVIEW.md` - RAG 方法總覽
- `GRAPH_RAG_INTEGRATION_COMPLETE.md` - Graph RAG 整合
- `MULTI_DATABASE_ARCHITECTURE.md` - 多資料庫架構
- `使用42種RAG組合指南.md` - 42 種 RAG 組合使用指南

### 資料管理

- `系統資料狀態報告.md` - 當前資料狀態
- `Data_Quality_Diagnosis_Report.md` - 資料品質診斷
- `ENHANCED-DATA-SOURCES-REPORT.md` - 增強資料源報告
- `HARVARD-INTEGRATION-REPORT.md` - 哈佛藝術博物館整合

### 修復報告

- `OpenWebUI上傳問題最終解決方案.md` - **最新修復** (2025-12-05)
- `OpenWebUI批次嵌入修復報告.md` - 技術詳細報告
- `Graph_RAG_Chinese_Query_Fix_Report.md` - 中文查詢修復
- `系統全面診斷報告.md` - 系統診斷

### 優化與實驗

- `Complete_Optimization_Report.md` - 完整優化報告
- `RAG_OPTIMIZATION_FINAL_REPORT.md` - RAG 優化最終報告
- `EXPERIMENT_README.md` - 實驗指南
- `多模態RAG系統架構.md` - 多模態 RAG 架構

### 快速開始

- `QUICK_START_GUIDE.md` - 快速開始指南
- `QUICK_REFERENCE.md` - 快速參考
- `快速開始指南.md` - 中文快速開始
- `快速開始-資料擴增.md` - 資料擴增快速開始

---

## 6. 快速恢復步驟

### 情境 1: 系統重啟後檢查

```bash
# 1. 檢查所有容器狀態
docker ps -a

# 2. 啟動未運行的容器
docker start art-history-openwebui art-history-chromadb art-history-neo4j art-history-ollama

# 3. 檢查容器健康狀態
docker ps --filter name=art-history --format "table {{.Names}}\t{{.Status}}"

# 4. 查看日誌 (如有問題)
docker logs art-history-openwebui --tail 50
```

### 情境 2: OpenWebUI 修復驗證

```bash
# 1. 驗證修復是否仍然有效
docker exec art-history-openwebui grep -A 5 "# Ollama 不支援批次嵌入" /app/backend/open_webui/retrieval/utils.py

# 2. 測試嵌入生成
python3 test_openwebui_upload_fix.py

# 3. 如需重新應用修復
bash fix_ollama_batch_embeddings.sh
```

### 情境 3: 恢復到修復前狀態

```bash
# 恢復備份文件
docker exec art-history-openwebui cp \
  /app/backend/open_webui/retrieval/utils.py.backup_20251205_184218 \
  /app/backend/open_webui/retrieval/utils.py

# 重啟容器
docker restart art-history-openwebui
```

### 情境 4: 檢查資料庫連接

```bash
# Neo4j
curl http://localhost:7474

# ChromaDB
curl http://localhost:8000/api/v1/heartbeat

# Ollama
curl http://localhost:11434/api/tags

# PostgreSQL
docker exec art-database-postgres psql -U art_user -d art_history_db -c "\dt"
```

### 情境 5: 訪問各服務

```
OpenWebUI:         http://localhost:8080
Neo4j Browser:     http://localhost:7474
ChromaDB:          http://localhost:8000
Ollama:            http://localhost:11434
Nginx (前端):      http://localhost:80
Elasticsearch:     http://localhost:9200
Grafana:           http://localhost:3001
```

---

## 7. 關鍵配置文件位置

### 容器內配置

```
OpenWebUI 配置:
  - /app/backend/open_webui/retrieval/utils.py (已修復)
  - /app/backend/data/webui.db (SQLite 資料庫)

Ollama 模型:
  - /root/.ollama/models/

ChromaDB 資料:
  - /chroma/chroma/
```

### 主機配置

```
Docker Compose:
  - ./docker-compose.yml
  - ./docker-compose.openwebui.yml
  - ./docker-compose.neo4j.yml

修復腳本:
  - ./fix_ollama_batch_embeddings.sh
  - ./test_openwebui_upload_fix.py

環境變數:
  - ./.env (包含所有密碼和 API 密鑰)
```

---

## 8. 重要注意事項

### ⚠️ 不可直接使用 CLI 匯入到 OpenWebUI

**原因**:
- CLI 匯入直接寫入 ChromaDB
- OpenWebUI 需要在 `webui.db` 的 `document` 表中註冊文檔
- 未註冊的文檔不會被 RAG 系統使用

**正確方法**:
1. 訪問 http://localhost:8080
2. 進入 Workspace → Knowledge
3. 選擇 Knowledge Base
4. 通過 Web 介面上傳文件

### ⚠️ RAG 不需要 GPU 重新訓練

**說明**:
- RAG (Retrieval-Augmented Generation) 是運行時檢索
- 使用的模型 (nomic-embed-text, LLM) 已經預訓練好
- 新增資料只需生成嵌入向量並儲存
- **無需任何模型參數更新或訓練**

### ✅ 已安裝的 Ollama 模型

可通過以下命令檢查:
```bash
docker exec art-history-ollama ollama list
```

常用模型:
- `nomic-embed-text:latest` - 嵌入模型 (768 維)
- 其他 LLM 模型 (根據實際安裝情況)

---

## 9. 故障排除快速參考

### OpenWebUI 無法上傳文件

1. 檢查容器狀態是否 healthy
2. 驗證修復是否有效 (見情境 2)
3. 查看日誌: `docker logs art-history-openwebui --tail 100`
4. 測試 Ollama 連接:
   ```bash
   docker exec art-history-openwebui curl http://art-history-ollama:11434/api/tags
   ```

### ChromaDB 連接失敗

1. 確認容器運行: `docker ps | grep chromadb`
2. 檢查端口: 應為 8000 而非 8001
3. 測試連接:
   ```bash
   curl http://localhost:8000/api/v1/heartbeat
   ```

### Neo4j 無法訪問

1. 檢查容器健康: `docker ps | grep neo4j`
2. 查看日誌: `docker logs art-history-neo4j --tail 50`
3. 確認密碼設定在 `.env` 文件中

### Ollama 模型無法載入

1. 檢查容器狀態: `docker ps | grep ollama`
2. 列出已安裝模型: `docker exec art-history-ollama ollama list`
3. 重新拉取模型:
   ```bash
   docker exec art-history-ollama ollama pull nomic-embed-text
   ```

---

## 10. 備份建議

### 定期備份項目

1. **Docker 資料卷** (最重要):
   ```bash
   # 備份所有資料卷
   docker run --rm -v art-history-database_openwebui_data:/data \
     -v $(pwd)/backup:/backup alpine \
     tar czf /backup/openwebui_data_$(date +%Y%m%d).tar.gz -C /data .
   ```

2. **配置文件**:
   - `.env` (包含所有密碼)
   - `docker-compose.yml` 及相關 compose 文件
   - 所有 `.sh` 腳本文件

3. **文檔**:
   - 所有 `.md` 文檔文件 (已超過 100 個)

4. **資料庫備份**:
   ```bash
   # Neo4j 備份
   docker exec art-history-neo4j neo4j-admin dump \
     --database=neo4j --to=/backups/neo4j_$(date +%Y%m%d).dump

   # PostgreSQL 備份
   docker exec art-database-postgres pg_dump \
     -U art_user art_history_db > backup_$(date +%Y%m%d).sql
   ```

---

## 11. 下次啟動檢查清單

- [ ] 檢查所有 Docker 容器是否運行
- [ ] 驗證 OpenWebUI 可以訪問 (http://localhost:8080)
- [ ] 驗證 Neo4j 可以訪問 (http://localhost:7474)
- [ ] 測試 Ollama 嵌入生成 (`python3 test_openwebui_upload_fix.py`)
- [ ] 檢查 OpenWebUI 修復是否仍有效
- [ ] 查看各容器日誌確認無錯誤
- [ ] 測試 RAG 功能是否正常

---

## 12. 聯絡資訊與資源

### 系統文檔

所有文檔位於: `/mnt/c/Users/ssking1999/Desktop/藝術史資料庫/art-history-database/`

### 重要 GitHub 儲存庫 (參考)

- OpenWebUI: https://github.com/open-webui/open-webui
- Ollama: https://github.com/ollama/ollama
- ChromaDB: https://github.com/chroma-core/chroma
- Neo4j: https://github.com/neo4j/neo4j

---

**備份完成時間**: 2025-12-06
**下次建議檢查**: 系統重啟後或重大配置變更時
**系統狀態**: ✅ 所有核心功能正常運作

---

## 附錄: 環境變數完整列表

```bash
# OpenWebUI 完整環境變數 (從容器提取)
DEFAULT_USER_ROLE=user
ENABLE_COMMUNITY_SHARING=false
WEBUI_LOG_LEVEL=INFO
CHUNK_OVERLAP=200
ENABLE_MODEL_FILTER=false
ENABLE_RAG_WEB_SEARCH=true
ENABLE_SIGNUP=true
WEBUI_AUTH=false
CHROMA_HTTP_PORT=8000
INTEGRATION_API_URL=http://host.docker.internal:8009
OPENAI_API_BASE_URLS=http://art-history-openwebui-integration:8009/v1
VECTOR_DB=chroma
RAG_EMBEDDING_MODEL=nomic-embed-text:latest
RAG_API_BASE_URL=http://host.docker.internal:8007
OLLAMA_BASE_URL=http://art-history-ollama:11434
ENABLE_RAG_LOCAL=true
OPENAI_API_BASE_URL=
RAG_TOP_K=5
OLLAMA_API_BASE_URL=http://art-history-ollama:11434
CHROMA_HTTP_HOST=art-history-chromadb
RAG_EMBEDDING_ENGINE=ollama
ENABLE_MESSAGE_RATING=true
MODEL_FILTER_ENABLED=false
ENABLE_IMAGE_GENERATION=false
CHUNK_SIZE=1000
OPENAI_API_KEY=sk-test-placeholder-please-replace
OPENAI_API_KEYS=sk-art-history-rag
ENV=prod
PORT=8080
USE_OLLAMA_DOCKER=false
USE_CUDA_DOCKER=false
USE_SLIM_DOCKER=false
SCARF_NO_ANALYTICS=true
DO_NOT_TRACK=true
ANONYMIZED_TELEMETRY=false
WHISPER_MODEL=base
DOCKER=true
```

---

**本文檔是系統配置的快照，用於快速檢查和恢復系統。**
**建議定期更新此文檔以反映系統變更。**
