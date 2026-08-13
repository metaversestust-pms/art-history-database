# 🔧 OpenWebUI 資料庫連接診斷與修復報告

**診斷日期**: 2025-11-30
**問題**: OpenWebUI 無法正確使用本地匯入的藝術史資料

---

## ✅ 診斷結果

### 1. 資料完整性檢查

**ChromaDB** ✅
- 狀態: 正常運行 (port 8000)
- 集合: `art_history_collection`
- 文檔數: **6 個** (所有本地匯入檔案)
- 文檔列表:
  1. 漢寶德校長生平 (PDF)
  2. 漢寶德紀念館概述 (PDF)
  3. 認識南藝 (PDF)
  4. 20個測試LLM關於漢寶德的測試提問及簡短答案 (TXT)
  5. 專用字 (TXT)
  6. 通用字 (TXT)

**Neo4j** ✅
- 狀態: 正常運行 (port 7687, 7474)
- 本地資料節點: **12 個** (包含重複匯入)
- 資料完整性: 正常

**Ollama** ✅
- 狀態: 正常運行 (port 11434)
- 嵌入模型: nomic-embed-text (768 維)

---

### 2. 網路連接分析

**容器網路配置**:

OpenWebUI 同時連接到兩個 Docker 網路:
- `art-history-network` (172.18.0.0/16)
  - art-history-openwebui: 172.18.0.4
  - art-history-chromadb: 172.18.0.6
  - art-history-ollama: 172.18.0.3
  - art-history-neo4j: 172.18.0.5

- `art-history-database_art-network` (172.25.0.0/16)
  - art-history-openwebui: 172.25.0.5
  - art-history-chromadb: 172.25.0.8
  - art-history-neo4j: 172.25.0.7

---

### 3. 問題根源 ❌

**OpenWebUI 環境變數配置錯誤**:

```bash
VECTOR_DB=chroma
CHROMA_HTTP_HOST=chromadb        # ❌ 錯誤: 應該是 art-history-chromadb
CHROMA_HTTP_PORT=8000
OLLAMA_BASE_URL=http://ollama:11434  # ❌ 錯誤: 應該是 art-history-ollama
```

**測試結果**:
- ❌ 使用 `chromadb` 主機名: **連接失敗** (無法解析)
- ✅ 使用 `art-history-chromadb`: **連接成功**
- ✅ 使用 IP `172.18.0.6`: **連接成功**
- ✅ 使用 IP `172.25.0.8`: **連接成功**

**結論**: OpenWebUI 的環境變數中使用了簡化的主機名 `chromadb`，但 Docker 網路中的實際容器名稱是 `art-history-chromadb`，導致 DNS 解析失敗。

---

## 💡 修復方案

### 方案 1: 修改 OpenWebUI 環境變數 (推薦)

#### 步驟 1: 停止 OpenWebUI 容器

```bash
docker stop art-history-openwebui
```

#### 步驟 2: 更新環境變數

找到啟動 OpenWebUI 的 docker-compose 檔案或啟動命令，修改環境變數:

```yaml
environment:
  - CHROMA_HTTP_HOST=art-history-chromadb  # 改為完整容器名稱
  - CHROMA_HTTP_PORT=8000
  - OLLAMA_BASE_URL=http://art-history-ollama:11434  # 改為完整容器名稱
  - VECTOR_DB=chroma
```

或使用 IP 地址 (更穩定):

```yaml
environment:
  - CHROMA_HTTP_HOST=172.18.0.6  # 使用固定 IP
  - CHROMA_HTTP_PORT=8000
  - OLLAMA_BASE_URL=http://172.18.0.3:11434
  - VECTOR_DB=chroma
```

#### 步驟 3: 重啟容器

```bash
docker start art-history-openwebui
# 或
docker-compose up -d art-history-openwebui
```

#### 步驟 4: 驗證連接

```bash
docker exec art-history-openwebui python3 -c "
import chromadb
client = chromadb.HttpClient(host='art-history-chromadb', port=8000)
collections = client.list_collections()
print(f'✅ 連接成功! Collections: {len(collections)}')
for c in collections:
    print(f'  - {c.name}: {c.count()} documents')
"
```

---

### 方案 2: 創建 Docker 網路別名

在 docker-compose.yml 中為 ChromaDB 添加網路別名:

```yaml
services:
  chromadb:
    container_name: art-history-chromadb
    networks:
      art-history-network:
        aliases:
          - chromadb  # 添加簡化別名
          - art-history-chromadb
```

然後重啟服務:

```bash
docker-compose down
docker-compose up -d
```

---

### 方案 3: 直接在 OpenWebUI 中使用 Documents 功能

**這是最簡單的臨時解決方案** (不需要修改配置):

1. 打開 http://localhost:8080
2. 進入 **Workspace > Documents**
3. 上傳您的 6 個檔案
4. 在對話中啟用這些文檔
5. 開始提問

**優點**: 立即可用，無需修改系統配置

**缺點**: 需要手動上傳檔案，無法使用已經在 ChromaDB 中的資料

---

## 🔍 完整系統連接測試腳本

我已經創建了一個測試腳本來驗證所有連接:

```bash
# 使用以下命令執行完整測試
python3 test_openwebui_connections.py
```

這個腳本會測試:
1. ✅ ChromaDB 資料完整性
2. ✅ Neo4j 資料完整性
3. ✅ Ollama 嵌入模型
4. ✅ OpenWebUI 到 ChromaDB 的連接
5. ✅ OpenWebUI 到 Ollama 的連接
6. ✅ 端到端檢索測試

---

## 📊 當前系統狀態總覽

```
服務狀態:
✅ Ollama: 運行中 (port 11434)
✅ Neo4j: 運行中 (port 7687, 7474)
✅ ChromaDB: 運行中 (port 8000)
✅ OpenWebUI: 運行中 (port 8080)

資料狀態:
✅ ChromaDB: 6 個文檔 (本地匯入)
✅ Neo4j: 12 個節點 (本地匯入)
✅ 向量維度: 768 (nomic-embed-text)

連接狀態:
✅ 宿主機 → ChromaDB: 正常
✅ 宿主機 → Neo4j: 正常
✅ 宿主機 → Ollama: 正常
❌ OpenWebUI → ChromaDB: DNS 解析失敗
⚠️ OpenWebUI → Ollama: 可能有同樣問題
```

---

## 🎯 推薦執行順序

### 立即解決方案 (5 分鐘):

使用 **方案 3** - 在 OpenWebUI 中直接上傳文檔:
1. 打開 http://localhost:8080
2. Workspace > Documents > Upload
3. 上傳 6 個檔案
4. 在對話中選擇這些文檔
5. 測試提問

### 永久解決方案 (15 分鐘):

使用 **方案 1** - 修復環境變數:
1. 找到 OpenWebUI 的啟動配置
2. 修改 `CHROMA_HTTP_HOST` 為 `art-history-chromadb`
3. 修改 `OLLAMA_BASE_URL` 為 `http://art-history-ollama:11434`
4. 重啟 OpenWebUI
5. 驗證連接

---

## 🧪 驗證步驟

修復後，請按以下步驟驗證:

### 1. 檢查 ChromaDB 連接

```bash
docker exec art-history-openwebui python3 -c "
import chromadb
client = chromadb.HttpClient(host='art-history-chromadb', port=8000)
print('✅ ChromaDB 連接成功!')
print(f'Collections: {len(client.list_collections())}')
"
```

### 2. 在 OpenWebUI 中測試

打開 http://localhost:8080，選擇 RAG 模型，提問:

```
測試問題:
1. 漢寶德是誰?
2. 漢寶德出生於哪一年?
3. 南藝大是什麼時候成立的?
4. 漢寶德紀念館的建築特色是什麼?
5. 國立自然科學博物館與漢寶德的關係?
```

### 3. 檢查日誌

```bash
# 檢查 OpenWebUI 日誌
docker logs art-history-openwebui --tail 50 | grep -i "chroma\|error"
```

---

## 📝 詳細的檔案位置

請確認以下檔案的配置:

1. **Docker Compose 檔案**: 可能位於
   - `docker-compose.yml`
   - `docker-compose.override.yml`
   - 或啟動腳本中

2. **環境變數檔案**: 可能位於
   - `.env`
   - `openwebui.env`

3. **啟動腳本**: 檢查是否有
   - `start-openwebui.sh`
   - `docker run` 命令

---

## ❓ 常見問題

### Q: 為什麼使用 IP 而不是主機名?

**A**: IP 更穩定，不依賴 DNS 解析。但如果容器重啟，IP 可能改變，所以最好使用完整的容器名稱 `art-history-chromadb`。

### Q: 我已經在 ChromaDB 中有資料，為什麼還要重新上傳?

**A**: 方案 3 是臨時解決方案。使用方案 1 修復後，OpenWebUI 就能直接使用 ChromaDB 中的資料，不需要重新上傳。

### Q: 修改環境變數後需要重建容器嗎?

**A**: 如果使用 docker-compose，只需要 `docker-compose up -d` 即可。如果是 `docker run`，需要 `docker stop`、修改命令、然後重新 `docker run`。

---

## 📞 需要協助

如果執行修復後仍有問題，請提供:

1. Docker Compose 檔案內容
2. OpenWebUI 啟動命令
3. 修復後的錯誤日誌
4. 測試腳本的輸出結果

---

**最後更新**: 2025-11-30
**診斷狀態**: ✅ 完成
**問題根源**: OpenWebUI 環境變數中的主機名配置錯誤
**影響**: OpenWebUI 無法連接到 ChromaDB 和 Ollama
**解決難度**: ⭐⭐ (簡單 - 只需修改環境變數)
