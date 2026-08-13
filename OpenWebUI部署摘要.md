# 🎨 OpenWebUI 部署配置完成摘要

## ✅ 已創建的文件

### Docker 配置
- ✅ `docker-compose.openwebui.yml` - OpenWebUI 服務配置
  - Ollama (LLM 引擎)
  - OpenWebUI (Web 界面)
  - ChromaDB (向量資料庫)

### 環境配置
- ✅ `.env.openwebui` - 環境變數模板
  - OpenAI API 配置（可選）
  - RAG 參數設定
  - 資料庫連接設定
  - 功能開關

### 部署腳本
- ✅ `start-openwebui.sh` - 一鍵啟動所有服務
- ✅ `download-models.sh` - 下載 LLM 模型
- ✅ `register-models.sh` - 註冊 RAG 模型組合
- ✅ `stop-openwebui.sh` - 停止服務
- ✅ `restart-openwebui.sh` - 重啟服務

### 文檔
- ✅ `OPENWEBUI_部署指南.md` - 完整部署文檔

---

## 🚀 快速部署（3 步驟）

### 步驟 1: 啟動服務
```bash
cd art-history-database
./start-openwebui.sh
```

**預期輸出**:
```
╔════════════════════════════════════════════════════════╗
║   🎨 藝術史資料庫 OpenWebUI 部署系統                  ║
╚════════════════════════════════════════════════════════╝

✅ Docker 環境正常
✅ docker-compose 已安裝
ℹ️  當前工作目錄: /path/to/art-history-database
✅ 目錄創建完成
✅ Docker 網路創建成功: art-history-network
✅ OpenWebUI 服務已啟動
✅ Ollama 服務就緒

📌 訪問地址：
   • OpenWebUI:     http://localhost:8080
   • Ollama API:    http://localhost:11434
   • Neo4j Browser: http://localhost:7474
   • ChromaDB:      http://localhost:8001
```

### 步驟 2: 下載模型
```bash
./download-models.sh
```

**將下載以下模型**:
- 🦙 Llama 3.1 8B (8GB)
- 🔮 Qwen 2.5 7B (7GB)
- 💎 Gemma 2 2B (2GB)
- 🧠 DeepSeek-R1 8B (8GB)
- 📊 Nomic Embed Text (274MB)

**預計下載時間**: 30-60 分鐘（取決於網速）

### 步驟 3: 註冊模型組合
```bash
./register-models.sh
```

**將自動**:
- 啟動 RAG 管理器 (Port 8007)
- 啟動 OpenWebUI 整合服務 (Port 8009)
- 註冊 30 種 RAG+LLM 組合

---

## 📋 服務清單

### 主要服務

| 服務名稱 | 容器名稱 | 端口 | 用途 |
|----------|----------|------|------|
| OpenWebUI | art-history-openwebui | 8080 | Web 用戶界面 |
| Ollama | art-history-ollama | 11434 | LLM 推理引擎 |
| ChromaDB | art-history-chromadb | 8001 | 向量資料庫 |
| Neo4j | art-history-neo4j | 7474, 7687 | 知識圖譜 |

### 背景服務

| 服務名稱 | 端口 | 日誌位置 |
|----------|------|----------|
| RAG Manager | 8007 | logs/rag_manager.log |
| Integration Service | 8009 | logs/openwebui_integration.log |

### 檢查服務狀態

```bash
# 查看所有容器
docker ps --filter "name=art-history"

# 檢查服務健康
curl http://localhost:8080        # OpenWebUI
curl http://localhost:11434/api/tags  # Ollama
curl http://localhost:8001/api/v1/heartbeat  # ChromaDB
curl http://localhost:8007/health  # RAG Manager
curl http://localhost:8009/health  # Integration
```

---

## 🎯 支援的功能

### RAG 策略（6 種）

1. **🔍 Vector Only** - 純向量語義檢索
   - 適合：語義相似度查詢
   - 速度：快

2. **🕸️ Graph Only** - Neo4j 知識圖譜檢索
   - 適合：關係推理、歷史脈絡
   - 特點：結構化知識

3. **⚖️ Hybrid Balanced** - 混合策略
   - 適合：綜合分析
   - 平衡：向量 + 圖譜

4. **🎯 Advanced RAG** - 多級檢索與重排序
   - 適合：複雜查詢
   - 特點：多輪精煉

5. **🤖 Agentic RAG** - 智能代理式推理
   - 適合：多步驟推理任務
   - 特點：自主規劃

6. **🔄 Self RAG** - 自我反思迭代改進
   - 適合：高準確性需求
   - 特點：自我修正

### LLM 模型（5 種）

1. **🦙 Llama 3.1 8B** - 通用能力，指令遵循
2. **🔮 Qwen 2.5 7B** - 中文優化，平衡性能
3. **💎 Gemma 2 2B** - 輕量級，快速響應
4. **🧠 DeepSeek-R1 8B** - 推理專家
5. **🤖 GPT-OSS 20B** - 開源 GPT（可選，需更多資源）

### 模型組合（5 × 6 = 30 種）

每個 LLM 模型都可以與 6 種 RAG 策略組合，提供 30 種不同的查詢體驗。

---

## 💡 使用示例

### 訪問 OpenWebUI

1. 打開瀏覽器：http://localhost:8080
2. 無需登入（已設置 WEBUI_AUTH=false）
3. 在左上角選擇模型組合

### 測試查詢

```
範例 1: 基礎查詢
模型: Llama 3.1 8B + 混合RAG
問題: 達文西有哪些著名的藝術作品？

範例 2: 關係探索
模型: Llama 3.1 8B + 圖譜RAG
問題: 文藝復興時期藝術家之間有什麼影響關係？

範例 3: 風格比較
模型: Llama 3.1 8B + Advanced RAG
問題: 比較巴洛克和洛可可藝術風格的異同

範例 4: 深度分析
模型: Llama 3.1 8B + Agentic RAG
問題: 分析印象派運動對現代藝術的影響

範例 5: 快速查詢
模型: Gemma 2 2B + 向量RAG
問題: 莫內最著名的作品是什麼？
```

### Neo4j 知識圖譜探索

1. 訪問：http://localhost:7474
2. 登入：neo4j / arthistory123
3. 執行查詢：

```cypher
// 查看資料庫統計
MATCH (n) RETURN labels(n) as Type, count(*) as Count

// 查看藝術家網絡
MATCH (a1:Artist)-[r:INFLUENCED]->(a2:Artist)
RETURN a1, r, a2
LIMIT 50

// 查看特定藝術家的作品
MATCH (artist:Artist {name: "Leonardo da Vinci"})-[:CREATED]->(artwork:Artwork)
RETURN artist, artwork
```

---

## 🔧 常用命令

### 服務管理

```bash
# 啟動所有服務
./start-openwebui.sh

# 停止服務
./stop-openwebui.sh

# 重啟服務
./restart-openwebui.sh

# 查看日誌
docker-compose -f docker-compose.openwebui.yml logs -f

# 查看特定服務日誌
docker logs art-history-openwebui -f
docker logs art-history-ollama -f
tail -f logs/rag_manager.log
```

### 模型管理

```bash
# 列出已下載的模型
docker exec art-history-ollama ollama list

# 下載新模型
docker exec art-history-ollama ollama pull <model-name>

# 刪除模型
docker exec art-history-ollama ollama rm <model-name>

# 測試模型
docker exec -it art-history-ollama ollama run llama3.1:8b "測試問題"
```

### 資料庫管理

```bash
# 進入 Neo4j 容器
docker exec -it art-history-neo4j bash

# 備份 Neo4j 資料
docker exec art-history-neo4j neo4j-admin dump --to=/backups/neo4j-backup.dump

# 進入 PostgreSQL
docker exec -it art-database-postgres psql -U art_user -d art_history_db
```

---

## ⚠️ 注意事項

### 系統要求

- **最低**: 16GB RAM, 50GB 硬碟
- **推薦**: 32GB RAM, 100GB SSD, NVIDIA GPU

### 資源佔用

**模型大小**:
- Llama 3.1 8B: ~8 GB
- Qwen 2.5 7B: ~7 GB
- Gemma 2 2B: ~2 GB
- DeepSeek-R1 8B: ~8 GB
- Nomic Embed: ~274 MB
- **總計**: ~25 GB

**運行時記憶體**:
- Ollama: 4-8 GB
- OpenWebUI: 512 MB - 1 GB
- ChromaDB: 512 MB
- Neo4j: 2-4 GB
- 其他服務: 2-4 GB
- **總計**: 10-20 GB

### 網路端口

確保以下端口未被佔用：
- 8080 (OpenWebUI)
- 11434 (Ollama)
- 8001 (ChromaDB)
- 8007 (RAG Manager)
- 8009 (Integration)
- 7474, 7687 (Neo4j)

---

## 🐛 故障排除

### 問題 1: Ollama 無法啟動

```bash
# 檢查日誌
docker logs art-history-ollama

# 如果是 GPU 問題（無 NVIDIA GPU）
# 編輯 docker-compose.openwebui.yml
# 刪除 deploy.resources.reservations.devices 部分

# 重啟容器
docker restart art-history-ollama
```

### 問題 2: 模型下載失敗

```bash
# 檢查網路
ping ollama.ai

# 手動下載（進入容器）
docker exec -it art-history-ollama bash
ollama pull llama3.1:8b
exit
```

### 問題 3: RAG 無法檢索資料

```bash
# 檢查 Neo4j
curl http://localhost:7474

# 檢查 RAG Manager
curl http://localhost:8007/health

# 重啟 RAG Manager
pkill -f unified_rag_manager.py
cd langchain-rag && python3 unified_rag_manager.py &
```

### 完全重置

```bash
# 停止所有服務
./stop-openwebui.sh
docker-compose down
docker-compose -f docker-compose.neo4j.yml down
docker-compose -f docker-compose.openwebui.yml down

# 刪除所有資料（警告：會刪除所有資料！）
docker-compose down -v
docker-compose -f docker-compose.neo4j.yml down -v
docker-compose -f docker-compose.openwebui.yml down -v

# 重新部署
./start-openwebui.sh
./download-models.sh
./register-models.sh
```

---

## 📞 技術支援

如遇問題：

1. 查看 `OPENWEBUI_部署指南.md` 完整文檔
2. 檢查日誌文件：
   - `logs/rag_manager.log`
   - `logs/openwebui_integration.log`
   - `docker logs art-history-openwebui`
3. 訪問項目文檔和 Issues

---

## 🎉 部署完成！

現在您可以：

✅ 使用 30 種 RAG+LLM 組合進行藝術史查詢
✅ 在 Neo4j Browser 中探索知識圖譜
✅ 通過 OpenWebUI 獲得智能問答體驗
✅ 自訂和擴展系統功能

**開始探索藝術史的奧秘吧！** 🎨

---

**最後更新**: 2025-10-15
**版本**: 1.0.0
