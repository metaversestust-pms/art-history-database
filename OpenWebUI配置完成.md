# ✅ OpenWebUI Docker 部署配置完成

## 🎉 配置狀態：已完成

所有 OpenWebUI 部署所需的配置文件和腳本已成功創建！

---

## 📁 已創建的文件清單

### 1. Docker 配置文件
- ✅ `docker-compose.openwebui.yml` - OpenWebUI 服務配置
  - 包含 Ollama、OpenWebUI、ChromaDB 三個服務
  - 配置了健康檢查和自動重啟
  - 支持 GPU 加速（可選）

### 2. 環境配置
- ✅ `.env.openwebui` - 環境變數模板
  - 完整的配置選項說明
  - 包含所有必要的環境變數
  - 可根據需求自訂

### 3. 自動化腳本（5 個）
- ✅ `start-openwebui.sh` - 一鍵啟動腳本
- ✅ `download-models.sh` - 模型下載腳本
- ✅ `register-models.sh` - 模型註冊腳本
- ✅ `stop-openwebui.sh` - 停止服務腳本
- ✅ `restart-openwebui.sh` - 重啟服務腳本

### 4. 文檔
- ✅ `OPENWEBUI_部署指南.md` - 完整部署文檔（60+ 頁）
- ✅ `OpenWebUI部署摘要.md` - 快速參考文檔
- ✅ `OpenWebUI配置完成.md` - 本文件

---

## 🚀 下一步：開始部署

### 方法一：自動化部署（推薦）

```bash
cd art-history-database

# 步驟 1: 啟動服務
bash start-openwebui.sh

# 步驟 2: 下載模型（約 30-60 分鐘）
bash download-models.sh

# 步驟 3: 註冊模型組合
bash register-models.sh
```

### 方法二：手動部署

```bash
cd art-history-database

# 1. 創建 Docker 網路
docker network create art-history-network

# 2. 啟動核心服務（如果尚未運行）
docker-compose up -d

# 3. 啟動 Neo4j
docker-compose -f docker-compose.neo4j.yml up -d

# 4. 啟動 OpenWebUI
docker-compose -f docker-compose.openwebui.yml up -d

# 5. 等待服務啟動
sleep 30

# 6. 下載模型
docker exec art-history-ollama ollama pull llama3.1:8b
docker exec art-history-ollama ollama pull qwen2.5:7b
docker exec art-history-ollama ollama pull gemma2:2b
docker exec art-history-ollama ollama pull nomic-embed-text

# 7. 啟動 RAG 管理器
cd langchain-rag
python3 unified_rag_manager.py &
cd ..

# 8. 啟動整合服務
python3 openwebui_integration.py &
```

---

## 📋 部署檢查清單

### 啟動前檢查

- [ ] Docker 已安裝且運行中
- [ ] Docker Compose 已安裝
- [ ] 至少 16GB RAM 可用
- [ ] 至少 50GB 硬碟空間
- [ ] 端口 8080, 11434, 8007, 8009 未被佔用

### 啟動後驗證

- [ ] OpenWebUI 可訪問 (http://localhost:8080)
- [ ] Ollama API 響應 (http://localhost:11434/api/tags)
- [ ] ChromaDB 運行中 (http://localhost:8001/api/v1/heartbeat)
- [ ] Neo4j 可訪問 (http://localhost:7474)
- [ ] RAG Manager 響應 (http://localhost:8007/health)
- [ ] Integration Service 響應 (http://localhost:8009/health)

### 功能測試

- [ ] 可以在 OpenWebUI 中看到模型列表
- [ ] 可以切換不同的 RAG 策略組合
- [ ] 提問後能獲得回答
- [ ] RAG 檢索正常工作
- [ ] Neo4j 知識圖譜可訪問

---

## 🎯 快速測試

### 測試 1: 檢查服務狀態

```bash
# 檢查所有容器
docker ps --filter "name=art-history"

# 應該看到以下容器運行中：
# - art-history-ollama
# - art-history-openwebui
# - art-history-chromadb
# - art-history-neo4j
# - art-database-postgres
# - art-database-redis
# - art-database-elasticsearch
```

### 測試 2: 訪問 Web 界面

```bash
# 在瀏覽器中打開
open http://localhost:8080
# 或
xdg-open http://localhost:8080  # Linux
start http://localhost:8080     # Windows
```

### 測試 3: 測試 Ollama 模型

```bash
# 列出已下載的模型
docker exec art-history-ollama ollama list

# 測試模型
docker exec art-history-ollama ollama run llama3.1:8b "用中文介紹達文西"
```

### 測試 4: 測試 RAG API

```bash
# 測試 RAG Manager
curl http://localhost:8007/health

# 測試整合服務
curl http://localhost:8009/health
```

### 測試 5: 測試 Neo4j

```bash
# 訪問 Neo4j Browser
open http://localhost:7474

# 登入憑證：
# Username: neo4j
# Password: arthistory123

# 執行測試查詢：
MATCH (n) RETURN count(n) as total_nodes;
```

---

## 📊 系統架構概覽

```
┌─────────────────────────────────────────────────────────┐
│                    使用者瀏覽器                          │
│                  http://localhost:8080                  │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   OpenWebUI (8080)                      │
│              Web 界面 + 模型選擇                         │
└─────┬──────────────┬──────────────┬────────────────────┘
      │              │              │
      ▼              ▼              ▼
┌──────────┐  ┌──────────┐  ┌──────────────┐
│  Ollama  │  │ChromaDB  │  │ Integration  │
│  (11434) │  │  (8001)  │  │   (8009)     │
└──────────┘  └──────────┘  └──────┬───────┘
                                   │
                                   ▼
                            ┌──────────────┐
                            │ RAG Manager  │
                            │   (8007)     │
                            └──────┬───────┘
                                   │
                    ┌──────────────┼──────────────┐
                    ▼              ▼              ▼
              ┌──────────┐  ┌──────────┐  ┌──────────┐
              │  Neo4j   │  │PostgreSQL│  │  Redis   │
              │ (7474/   │  │  (5432)  │  │  (6379)  │
              │  7687)   │  │          │  │          │
              └──────────┘  └──────────┘  └──────────┘
```

---

## 🔑 重要信息

### 訪問地址

| 服務 | URL | 用途 |
|------|-----|------|
| OpenWebUI | http://localhost:8080 | Web 界面 |
| Ollama API | http://localhost:11434 | LLM API |
| ChromaDB | http://localhost:8001 | 向量資料庫 |
| Neo4j Browser | http://localhost:7474 | 知識圖譜 |
| RAG Manager | http://localhost:8007 | RAG API |
| Integration | http://localhost:8009 | 整合服務 |

### 默認憑證

- **Neo4j**:
  - Username: `neo4j`
  - Password: `arthistory123`

- **PostgreSQL**:
  - Username: `art_user`
  - Password: 在 `.env` 中配置

- **OpenWebUI**:
  - 認證已禁用 (WEBUI_AUTH=false)
  - 無需登入即可使用

### 資料存儲位置

- **Ollama 模型**: Docker volume `ollama_data`
- **OpenWebUI 資料**: Docker volume `openwebui_data`
- **ChromaDB 資料**: Docker volume `chromadb_data`
- **Neo4j 資料**: Docker volume `neo4j_data`
- **日誌文件**: `./logs/`

---

## 💡 使用提示

### 1. 選擇合適的模型組合

根據查詢類型選擇：

- **快速查詢**: Gemma 2 2B + Vector RAG
- **一般查詢**: Llama 3.1 8B + Hybrid RAG
- **關係探索**: Llama 3.1 8B + Graph RAG
- **深度分析**: Llama 3.1 8B + Agentic RAG
- **高準確性**: Llama 3.1 8B + Self RAG

### 2. 優化性能

```bash
# 限制 Ollama 記憶體使用
# 編輯 docker-compose.openwebui.yml
services:
  ollama:
    deploy:
      resources:
        limits:
          memory: 8G  # 根據系統調整
```

### 3. 查看日誌

```bash
# 實時查看所有日誌
docker-compose -f docker-compose.openwebui.yml logs -f

# 查看特定服務
docker logs art-history-openwebui -f
docker logs art-history-ollama -f

# 查看背景服務日誌
tail -f logs/rag_manager.log
tail -f logs/openwebui_integration.log
```

### 4. 管理模型

```bash
# 列出模型
docker exec art-history-ollama ollama list

# 下載新模型
docker exec art-history-ollama ollama pull <model-name>

# 刪除模型
docker exec art-history-ollama ollama rm <model-name>

# 查看模型詳情
docker exec art-history-ollama ollama show <model-name>
```

---

## 🐛 常見問題

### Q1: 腳本無法執行（權限錯誤）

**A**: 在 WSL/Windows 環境下，使用 `bash` 命令執行：

```bash
bash start-openwebui.sh
# 而不是
./start-openwebui.sh
```

### Q2: Ollama 無法使用 GPU

**A**: 如果沒有 NVIDIA GPU，編輯 `docker-compose.openwebui.yml`，刪除以下部分：

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all
          capabilities: [gpu]
```

### Q3: 端口被佔用

**A**: 修改 `docker-compose.openwebui.yml` 中的端口映射：

```yaml
ports:
  - "8081:8080"  # 改為 8081 或其他未使用的端口
```

### Q4: 記憶體不足

**A**:
1. 只下載必要的模型（例如只下載 Gemma 2 2B）
2. 限制服務記憶體使用
3. 關閉不需要的服務

### Q5: 無法連接到 Neo4j

**A**:
```bash
# 確認 Neo4j 運行中
docker ps | grep neo4j

# 重啟 Neo4j
docker restart art-history-neo4j

# 檢查日誌
docker logs art-history-neo4j
```

---

## 📚 進一步學習

### 文檔資源

- 📖 `OPENWEBUI_部署指南.md` - 完整部署指南
- 📄 `OpenWebUI部署摘要.md` - 快速參考
- 📋 `OPENWEBUI_SETUP_GUIDE.md` - 設置指南

### 相關文檔

- Neo4j 使用指南: `Neo4j使用指南.md`
- RAG 框架手冊: `RAG框架使用手冊.md`
- Docker 管理指南: `Docker服務管理指南.md`

### 在線資源

- OpenWebUI 官方文檔: https://docs.openwebui.com/
- Ollama 模型庫: https://ollama.ai/library
- Neo4j 學習中心: https://neo4j.com/graphacademy/

---

## 🎊 恭喜！

您已經成功完成 OpenWebUI 的 Docker 部署配置！

### 現在您可以：

✅ 使用一鍵腳本快速部署整個系統
✅ 下載和管理多個 LLM 模型
✅ 使用 30 種 RAG+LLM 組合
✅ 通過 Web 界面進行藝術史查詢
✅ 探索 Neo4j 知識圖譜
✅ 自訂和擴展系統功能

### 下一步：

1. 執行 `bash start-openwebui.sh` 開始部署
2. 執行 `bash download-models.sh` 下載模型
3. 執行 `bash register-models.sh` 註冊模型組合
4. 訪問 http://localhost:8080 開始使用！

**祝您探索愉快！** 🎨✨

---

**創建日期**: 2025-10-15
**配置版本**: 1.0.0
**狀態**: ✅ 已完成
