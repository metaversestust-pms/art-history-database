# OpenWebUI 與 Neo4j GraphRAG 集成配置指南

## 概述

本指南說明如何將OpenWebUI配置為使用我們的Neo4j GraphRAG系統，讓用戶可以通過OpenWebUI界面查詢藝術史知識圖譜。

## 架構

```
OpenWebUI (端口3001)
    ↓
OpenWebUI RAG集成服務 (端口8009)
    ↓
統一RAG管理API (端口8002)
    ↓
Neo4j GraphRAG + 向量檢索 (端口7687/7474)
```

## 服務狀態

- ✅ Neo4j數據庫: 運行中 (端口7687, 7474)
- ✅ 統一RAG管理API: 運行中 (端口8002)
- ✅ OpenWebUI RAG集成服務: 運行中 (端口8009)
- ✅ OpenWebUI: 運行中 (端口3001)

## 配置方法

### 方法1: 通過環境變量配置OpenWebUI

要讓OpenWebUI使用我們的GraphRAG系統，需要設置以下環境變量：

```bash
# 停止當前的OpenWebUI容器
docker stop openwebui-rag

# 重新啟動OpenWebUI，指向我們的RAG集成服務
docker run -d \
  --name openwebui-rag-updated \
  -p 3001:8080 \
  -e RAG_API_BASE_URL="http://host.docker.internal:8009" \
  -e RAG_API_KEY="" \
  -e RAG_EMBEDDING_ENGINE="http://host.docker.internal:8009/rag" \
  -e WEBUI_SECRET_KEY="your-secret-key" \
  -v open-webui:/app/backend/data \
  --add-host=host.docker.internal:host-gateway \
  ghcr.io/open-webui/open-webui:main
```

### 方法2: 通過OpenWebUI管理界面配置

1. 打開OpenWebUI管理界面: http://localhost:3001
2. 進入 Settings > RAG
3. 配置RAG提供者:
   - **RAG API Base URL**: `http://localhost:8009`
   - **RAG API Endpoint**: `/rag/query`
   - **Collection Name**: `art_history_knowledge_graph`

### 方法3: 直接測試集成API

可以直接使用我們的集成API進行測試：

```bash
# 健康檢查
curl http://localhost:8009/health

# RAG查詢測試
curl -X POST "http://localhost:8009/rag/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "達文西有哪些著名作品？",
    "top_k": 5
  }'

# 獲取配置信息
curl http://localhost:8009/rag/config
```

## 功能特色

我們的GraphRAG集成提供了以下功能：

1. **多策略查詢**:
   - vector_only: 純向量檢索
   - graph_only: 純知識圖譜查詢
   - hybrid_balanced: 混合策略
   - adaptive: 自適應策略
   - specialized: 專門化策略

2. **知識圖譜數據**:
   - 5位知名藝術家 (達文西、米開朗基羅、莫奈、梵高、畢卡索)
   - 5件藝術作品
   - 4個藝術運動
   - 3個地理位置
   - 3個博物館

3. **實時性能監控**:
   - 查詢處理時間
   - 信心分數
   - 快取命中率
   - 策略性能統計

## API端點

### OpenWebUI RAG集成服務 (端口8009)

- `GET /` - 服務狀態
- `GET /health` - 健康檢查
- `POST /rag/query` - RAG查詢 (OpenWebUI格式)
- `GET /rag/collections` - 獲取可用集合
- `GET /rag/config` - 獲取RAG配置

### 統一RAG管理API (端口8002)

- `GET /health` - 健康檢查
- `POST /query` - 原生RAG查詢
- `GET /system/status` - 系統狀態
- `GET /system/strategies` - 可用策略

## 測試範例查詢

以下是一些測試查詢範例：

1. **藝術家相關**:
   - "達文西有哪些著名作品？"
   - "米開朗基羅和達文西有什麼關係？"
   - "印象派有哪些代表藝術家？"

2. **藝術運動**:
   - "印象派藝術運動的特點是什麼？"
   - "文藝復興時期的藝術特色"
   - "現代主義對藝術的影響"

3. **博物館和收藏**:
   - "羅浮宮收藏了哪些重要作品？"
   - "大都會博物館的著名展品"

## 故障排除

如果遇到問題，請檢查：

1. **服務連接**:
   ```bash
   curl http://localhost:8002/health  # 統一RAG管理API
   curl http://localhost:8009/health  # OpenWebUI集成服務
   ```

2. **Neo4j連接**:
   ```bash
   docker logs art-history-neo4j
   ```

3. **端口占用**:
   ```bash
   ss -tulnp | grep -E ':(8002|8009|3001|7687|7474)'
   ```

## 日誌監控

- 統一RAG管理API日誌: 查看後台進程
- OpenWebUI集成服務日誌: 查看後台進程
- Neo4j日誌: `docker logs art-history-neo4j`
- OpenWebUI日誌: `docker logs openwebui-rag`