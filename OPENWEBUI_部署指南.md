# 🎨 藝術史資料庫 - OpenWebUI 完整部署指南

## 📋 目錄

1. [系統要求](#系統要求)
2. [快速開始](#快速開始)
3. [詳細部署步驟](#詳細部署步驟)
4. [服務說明](#服務說明)
5. [使用指南](#使用指南)
6. [故障排除](#故障排除)
7. [進階配置](#進階配置)

---

## 🖥️ 系統要求

### 硬體需求

**最低配置**：
- CPU: 4 核心
- RAM: 16 GB
- 硬碟: 50 GB 可用空間
- GPU: 可選（推薦 NVIDIA GPU 8GB+ VRAM）

**推薦配置**：
- CPU: 8 核心或以上
- RAM: 32 GB 或以上
- 硬碟: 100 GB SSD
- GPU: NVIDIA RTX 3060 或以上（12GB+ VRAM）

### 軟體需求

- **作業系統**:
  - Ubuntu 20.04+ / Debian 11+
  - macOS 12+
  - Windows 10+ (with WSL2)

- **必要軟體**:
  - Docker 20.10+
  - Docker Compose 2.0+
  - Python 3.9+
  - Node.js 16+ (用於網路爬蟲)
  - curl
  - git

### 網路需求

- 穩定的網際網路連接（用於下載模型）
- 開放端口：
  - 8080 (OpenWebUI)
  - 11434 (Ollama)
  - 8007 (RAG Manager)
  - 8009 (Integration Service)
  - 7474, 7687 (Neo4j)
  - 5432 (PostgreSQL)
  - 6379 (Redis)
  - 9200 (Elasticsearch)

---

## 🚀 快速開始

### 一鍵部署（3 步驟）

```bash
# 1. 啟動所有服務
./start-openwebui.sh

# 2. 下載 LLM 模型
./download-models.sh

# 3. 註冊 RAG 模型組合
./register-models.sh
```

### 訪問系統

部署完成後，在瀏覽器中訪問：

- **OpenWebUI**: http://localhost:8080
- **Neo4j Browser**: http://localhost:7474 (用戶名: neo4j, 密碼: arthistory123)
- **RAG Manager API**: http://localhost:8007/docs

---

## 📝 詳細部署步驟

### 步驟 1: 準備環境

#### 1.1 克隆或進入專案目錄

```bash
cd art-history-database
```

#### 1.2 檢查 Docker 環境

```bash
# 檢查 Docker 版本
docker --version
docker-compose --version

# 確保 Docker daemon 運行中
docker info
```

#### 1.3 設置環境變數（可選）

```bash
# 複製環境變數模板
cp .env.openwebui .env

# 編輯環境變數（如需自訂）
nano .env
```

### 步驟 2: 啟動服務

#### 2.1 使用啟動腳本（推薦）

```bash
# 賦予執行權限
chmod +x start-openwebui.sh download-models.sh register-models.sh stop-openwebui.sh restart-openwebui.sh

# 執行啟動腳本
./start-openwebui.sh
```

腳本會自動：
- ✅ 創建必要的目錄結構
- ✅ 創建 Docker 網路
- ✅ 啟動核心服務（PostgreSQL, Redis, Elasticsearch）
- ✅ 啟動 Neo4j 知識圖譜
- ✅ 啟動 Ollama 和 OpenWebUI
- ✅ 檢查服務健康狀態

#### 2.2 手動啟動（進階用戶）

```bash
# 創建網路
docker network create art-history-network

# 啟動核心服務
docker-compose up -d

# 啟動 Neo4j
docker-compose -f docker-compose.neo4j.yml up -d

# 啟動 OpenWebUI
docker-compose -f docker-compose.openwebui.yml up -d
```

#### 2.3 檢查服務狀態

```bash
# 查看所有容器
docker ps

# 查看服務日誌
docker-compose -f docker-compose.openwebui.yml logs -f
```

### 步驟 3: 下載 LLM 模型

#### 3.1 使用下載腳本

```bash
./download-models.sh
```

#### 3.2 手動下載

```bash
# 進入 Ollama 容器
docker exec -it art-history-ollama bash

# 下載模型
ollama pull llama3.1:8b
ollama pull qwen2.5:7b
ollama pull gemma2:2b
ollama pull nomic-embed-text

# 查看已下載的模型
ollama list

# 退出容器
exit
```

#### 3.3 測試模型

```bash
# 測試 Llama 模型
docker exec art-history-ollama ollama run llama3.1:8b "用中文介紹達文西"
```

### 步驟 4: 啟動 RAG 服務

#### 4.1 啟動 RAG 管理器

```bash
cd langchain-rag
python3 unified_rag_manager.py &
cd ..
```

服務將運行在：http://localhost:8007

#### 4.2 啟動 OpenWebUI 整合服務

```bash
python3 openwebui_integration.py &
```

服務將運行在：http://localhost:8009

#### 4.3 使用註冊腳本（自動）

```bash
./register-models.sh
```

此腳本會自動：
- 啟動 RAG 管理器
- 啟動整合服務
- 註冊所有模型組合
- 驗證服務狀態

### 步驟 5: 配置 OpenWebUI

#### 5.1 首次訪問

1. 打開瀏覽器訪問：http://localhost:8080
2. 由於設置了 `WEBUI_AUTH=false`，無需登入即可使用

#### 5.2 上傳 RAG 函數（如果自動註冊失敗）

1. 點擊右上角設定圖標
2. 進入 **Settings** > **Functions**
3. 點擊 **+ Add Function**
4. 上傳文件：`enhanced_openwebui_rag_function_v3.py`
5. 啟用該函數

#### 5.3 驗證模型可見性

在左上角的模型選擇器中，應該能看到：

- 🔍 Llama 3.1 8B + 向量RAG
- 🕸️ Llama 3.1 8B + 圖譜RAG
- ⚖️ Llama 3.1 8B + 混合RAG
- 🎯 Llama 3.1 8B + Advanced RAG
- 🤖 Llama 3.1 8B + Agentic RAG
- 🔄 Llama 3.1 8B + Self RAG
- ... 等 30 種組合

---

## 🔧 服務說明

### 核心服務

| 服務 | 端口 | 說明 | 狀態檢查 |
|------|------|------|----------|
| OpenWebUI | 8080 | Web 界面 | http://localhost:8080 |
| Ollama | 11434 | LLM 引擎 | http://localhost:11434/api/tags |
| ChromaDB | 8001 | 向量資料庫 | http://localhost:8001/api/v1/heartbeat |
| RAG Manager | 8007 | RAG API | http://localhost:8007/health |
| Integration | 8009 | 整合服務 | http://localhost:8009/health |

### 資料庫服務

| 服務 | 端口 | 說明 | 狀態檢查 |
|------|------|------|----------|
| Neo4j | 7474, 7687 | 知識圖譜 | http://localhost:7474 |
| PostgreSQL | 5432 | 關聯式資料庫 | - |
| Redis | 6379 | 快取 | - |
| Elasticsearch | 9200 | 搜索引擎 | http://localhost:9200 |

### 背景服務

- **RAG Manager**: 管理所有 RAG 策略
- **OpenWebUI Integration**: 連接 OpenWebUI 和 RAG 系統
- **Web Crawler Agent**: 定期爬取藝術史資料（可選）

---

## 📚 使用指南

### 基本使用

#### 1. 選擇模型組合

在 OpenWebUI 左上角點擊模型選擇器，選擇合適的組合：

**推薦組合**：
- **一般查詢**: Llama 3.1 8B + 混合RAG
- **關係探索**: Llama 3.1 8B + 圖譜RAG
- **快速回答**: Gemma 2 2B + 向量RAG
- **深度分析**: Llama 3.1 8B + Agentic RAG

#### 2. 提出問題

在輸入框中輸入藝術史相關問題：

```
範例問題：
• 達文西有哪些著名的藝術作品？
• 文藝復興時期的藝術特點是什麼？
• 比較巴洛克和洛可可藝術風格的差異
• 印象派畫家莫內的代表作有哪些？
• 畢卡索的藝術風格是如何演變的？
```

#### 3. 查看 RAG 檢索結果

回答中會包含：
- 📝 主要答案
- 🔍 RAG 檢索到的相關資料
- 📊 使用的 RAG 策略信息
- 🔗 相關資料來源

### 進階使用

#### 使用 Neo4j 探索知識圖譜

1. 訪問：http://localhost:7474
2. 登入（neo4j/arthistory123）
3. 執行 Cypher 查詢：

```cypher
// 查看所有藝術家
MATCH (a:Artist) RETURN a LIMIT 10;

// 查看藝術家和作品關係
MATCH (artist:Artist)-[:CREATED]->(artwork:Artwork)
RETURN artist.name, artwork.title
LIMIT 20;

// 查看藝術風格影響關係
MATCH path=(s1:Style)-[:INFLUENCED*1..3]->(s2:Style)
RETURN path
LIMIT 5;

// 查看特定時期的藝術家
MATCH (p:Period {name: "Renaissance"})<-[:BELONGS_TO]-(a:Artist)
RETURN a.name, a.nationality
```

#### 使用 RAG Manager API

```bash
# 獲取 API 文檔
open http://localhost:8007/docs

# 測試向量檢索
curl -X POST http://localhost:8007/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "達文西的蒙娜麗莎",
    "strategy": "vector_only",
    "top_k": 5
  }'

# 測試圖譜檢索
curl -X POST http://localhost:8007/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "文藝復興時期的藝術家",
    "strategy": "graph_only"
  }'
```

---

## 🔍 故障排除

### 常見問題

#### 1. Ollama 無法啟動

**症狀**: `curl http://localhost:11434/api/tags` 無響應

**解決方案**:
```bash
# 檢查容器狀態
docker ps -a | grep ollama

# 查看日誌
docker logs art-history-ollama

# 重啟容器
docker restart art-history-ollama

# 如果是 GPU 問題（沒有 NVIDIA GPU）
# 編輯 docker-compose.openwebui.yml，刪除 deploy.resources 部分
```

#### 2. OpenWebUI 無法連接 Ollama

**症狀**: OpenWebUI 顯示 "Cannot connect to Ollama"

**解決方案**:
```bash
# 檢查網路連接
docker network inspect art-history-network

# 確保兩個容器在同一網路
docker network connect art-history-network art-history-ollama
docker network connect art-history-network art-history-openwebui

# 重啟 OpenWebUI
docker restart art-history-openwebui
```

#### 3. 模型下載失敗

**症狀**: `ollama pull` 超時或失敗

**解決方案**:
```bash
# 檢查網路連接
ping ollama.ai

# 使用代理（如果需要）
docker exec art-history-ollama bash -c \
  "export HTTP_PROXY=http://your-proxy:port && ollama pull llama3.1:8b"

# 手動下載（在主機上）
# 下載模型文件後，複製到容器
```

#### 4. RAG 檢索無結果

**症狀**: 問答系統無法檢索到相關資料

**解決方案**:
```bash
# 檢查 Neo4j 是否有資料
curl http://localhost:7474

# 在 Neo4j Browser 中檢查節點數量
# MATCH (n) RETURN count(n)

# 檢查 ChromaDB
curl http://localhost:8001/api/v1/heartbeat

# 重新導入資料
cd langchain-rag
python3 import_crawler_data_to_neo4j.py
```

#### 5. 記憶體不足

**症狀**: 服務崩潰或系統變慢

**解決方案**:
```bash
# 查看記憶體使用
docker stats

# 限制 Ollama 記憶體（編輯 docker-compose.openwebui.yml）
services:
  ollama:
    deploy:
      resources:
        limits:
          memory: 8G

# 只下載較小的模型
# gemma2:2b (2GB) 而不是 llama3.1:70b (40GB)
```

### 日誌檢查

```bash
# OpenWebUI 日誌
docker logs art-history-openwebui -f

# Ollama 日誌
docker logs art-history-ollama -f

# RAG Manager 日誌
tail -f logs/rag_manager.log

# 整合服務日誌
tail -f logs/openwebui_integration.log

# 所有服務日誌
docker-compose -f docker-compose.openwebui.yml logs -f
```

### 重置系統

如果遇到無法解決的問題：

```bash
# 停止所有服務
./stop-openwebui.sh
docker-compose down

# 刪除所有容器和資料（警告：會刪除所有資料）
docker-compose down -v
docker-compose -f docker-compose.neo4j.yml down -v
docker-compose -f docker-compose.openwebui.yml down -v

# 重新部署
./start-openwebui.sh
./download-models.sh
./register-models.sh
```

---

## ⚙️ 進階配置

### 自訂模型組合

編輯 `openwebui-config/models.json` 添加新組合：

```json
{
  "id": "custom-model",
  "name": "🎨 Custom Model + RAG",
  "description": "自訂模型組合",
  "meta": {
    "base_model": "your-model:tag",
    "rag_strategy": "hybrid_balanced"
  },
  "params": {
    "use_rag": true,
    "rag_strategy": "hybrid_balanced",
    "temperature": 0.2
  }
}
```

### 調整 RAG 參數

編輯 `.env` 文件：

```bash
# RAG 檢索數量
RAG_TOP_K=10

# 文本切分大小
CHUNK_SIZE=1500
CHUNK_OVERLAP=300

# 嵌入模型
RAG_EMBEDDING_MODEL=nomic-embed-text
```

### GPU 加速配置

確保已安裝 NVIDIA Docker Runtime：

```bash
# 安裝 nvidia-docker2
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker

# 測試 GPU 訪問
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

### 啟用認證

如需啟用用戶認證，編輯 `docker-compose.openwebui.yml`：

```yaml
environment:
  - WEBUI_AUTH=true
  - ENABLE_SIGNUP=false  # 禁止註冊
  - DEFAULT_USER_ROLE=user
```

重啟服務後，首次訪問會要求創建管理員帳戶。

---

## 📞 技術支援

如遇問題，請：

1. 查看本文檔的故障排除章節
2. 檢查日誌文件
3. 訪問項目 GitHub Issues
4. 提供以下信息：
   - 錯誤訊息和日誌
   - 系統環境（OS, Docker 版本）
   - 部署步驟

---

## 🎉 恭喜！

您已成功部署藝術史資料庫 OpenWebUI 系統！

現在可以：
- ✅ 使用 30 種 RAG+LLM 組合
- ✅ 探索藝術史知識圖譜
- ✅ 進行多模態藝術史查詢
- ✅ 自訂和擴展系統功能

**開始探索藝術史的奧秘吧！** 🎨
