# 🎯 後續步驟：為 OpenWebUI 添加 RAG 功能

**當前狀態**: ✅ OpenWebUI 已正常運行（端口 8080）
**下一步**: 添加 RAG+LLM 組合模型功能

---

## 📊 當前系統狀態

### ✅ 已完成
- OpenWebUI 運行正常（http://localhost:8080）
- 無認證問題
- 資料庫全新、乾淨

### ⏳ 待完成
- 連接 Ollama RAG Proxy（端口 11435）
- 在 OpenWebUI 中看到 RAG 組合模型
- 測試 RAG 查詢功能

---

## 🔧 步驟 1：驗證後端服務運行狀態

在執行任何操作前，先確認所有後端服務正常：

```bash
# 檢查所有服務
echo "1. Ollama RAG Proxy (11435):"
curl -s http://localhost:11435/health && echo "  ✅ 運行中" || echo "  ❌ 未運行"

echo ""
echo "2. Multi-DB RAG Server (8010):"
curl -s http://localhost:8010/health && echo "  ✅ 運行中" || echo "  ❌ 未運行"

echo ""
echo "3. Ollama (11434):"
curl -s http://localhost:11434/api/tags > /dev/null && echo "  ✅ 運行中" || echo "  ❌ 未運行"

echo ""
echo "4. Neo4j (7474):"
curl -s http://localhost:7474 > /dev/null && echo "  ✅ 運行中" || echo "  ❌ 未運行"

echo ""
echo "5. ChromaDB (8001):"
curl -s http://localhost:8001/api/v1/heartbeat > /dev/null && echo "  ✅ 運行中" || echo "  ❌ 未運行"
```

**如果有服務未運行，請先啟動它們**：

```bash
# 啟動 Ollama RAG Proxy
cd /mnt/c/Users/ssking1999/Desktop/藝術史資料庫/art-history-database
node ollama-rag-proxy.js > ollama-rag-proxy.log 2>&1 &

# 啟動 Multi-DB RAG Server
node multi-database-rag-server.js > multi-database-rag-server.log 2>&1 &

# 檢查 Docker 服務
docker ps | grep -E "neo4j|chromadb|ollama"
```

---

## 🔧 步驟 2：配置 OpenWebUI 連接到 Ollama RAG Proxy

### 方法 A：通過 OpenWebUI 界面添加（推薦）

1. **訪問 OpenWebUI**: http://localhost:8080

2. **進入設置**:
   - 點擊左下角的設置圖標（齒輪）
   - 或點擊用戶頭像 → Settings

3. **找到 Connections 或 Admin Settings**:
   - 在設置菜單中尋找 "Connections" 或 "External Connections"
   - 或者 "Admin Settings" → "Connections"

4. **添加 Ollama 連接**:
   ```
   名稱: RAG Proxy
   類型: Ollama
   URL: http://172.26.104.197:11435
   ```
   （使用 WSL2 IP 地址，而非 localhost）

5. **保存並測試**:
   - 點擊 "Save" 或 "Test Connection"
   - 應該看到連接成功的提示

### 方法 B：重新啟動容器並設置環境變量（自動化）

如果界面方法不可行，使用此方法：

```bash
# 獲取 WSL2 IP
WSL_IP=$(ip addr show eth0 | grep "inet " | awk '{print $2}' | cut -d/ -f1)
echo "WSL2 IP: $WSL_IP"

# 停止當前容器
docker stop art-history-openwebui
docker rm art-history-openwebui

# 重新啟動並添加 Ollama 連接
docker run -d \
  --name art-history-openwebui \
  --restart always \
  -p 8080:8080 \
  -e OLLAMA_BASE_URL=http://${WSL_IP}:11435 \
  -e WEBUI_AUTH=false \
  -v open-webui:/app/backend/data \
  ghcr.io/open-webui/open-webui:main

# 等待啟動
sleep 15

# 驗證
curl http://localhost:8080
```

---

## 🔧 步驟 3：驗證 RAG 模型是否可見

### 3.1 在終端驗證

```bash
# 獲取 WSL2 IP
WSL_IP=$(ip addr show eth0 | grep "inet " | awk '{print $2}' | cut -d/ -f1)

# 從 OpenWebUI 容器內測試連接
docker exec art-history-openwebui curl -s http://${WSL_IP}:11435/health

# 檢查模型列表
docker exec art-history-openwebui curl -s http://${WSL_IP}:11435/api/tags | grep -o '"name":"[^"]*-vector_rag"' | head -5
```

**預期輸出**:
```
"name":"llama3.1-vector_rag"
"name":"qwen2.5-vector_rag"
"name":"gemma2-vector_rag"
```

### 3.2 在 OpenWebUI 界面驗證

1. 訪問 http://localhost:8080
2. 點擊 "New Chat" 或 "+"
3. 查看模型下拉菜單
4. **應該看到 RAG 組合模型**:
   - llama3.1-vector_rag
   - llama3.1-graph_rag
   - qwen2.5-hybrid_rag
   - 等等...

---

## 🔧 步驟 4：測試 RAG 查詢

### 4.1 選擇 RAG 模型

在 OpenWebUI 中：
1. 選擇一個 RAG 模型（推薦：`llama3.1-vector_rag`）
2. 確認模型名稱顯示正確

### 4.2 提問測試

試試以下問題：

```
莫內的代表作品有哪些？
```

```
印象派和後印象派的區別是什麼？
```

```
文藝復興時期的藝術特點？
```

### 4.3 驗證回答格式

**正確的回答應該包含**:

```
[主要回答內容]

---

📊 **檢索信息**
- 🔍 RAG 策略: vector_rag
- 💾 資料庫: ChromaDB優先
- 🤖 LLM 模型: llama3.1:8b
- 📚 檢索來源: X 個

**參考資料來源:**
1. 📊 CHROMADB > Met Museum API
   🎯 相關度: 0.XX | 方法: vector
...
```

---

## 🐛 故障排除

### 問題 1: 看不到 RAG 組合模型

**可能原因**: OpenWebUI 無法連接到 Ollama RAG Proxy

**診斷**:
```bash
# 檢查 Proxy 是否運行
curl http://localhost:11435/health

# 檢查容器能否訪問
WSL_IP=$(ip addr show eth0 | grep "inet " | awk '{print $2}' | cut -d/ -f1)
docker exec art-history-openwebui curl -s http://${WSL_IP}:11435/health
```

**解決方案**:
- 如果 Proxy 未運行，重新啟動它
- 如果容器無法訪問，使用步驟 2 方法 B 重新配置

### 問題 2: Ollama RAG Proxy 未運行

**症狀**: `curl http://localhost:11435/health` 無回應

**解決方案**:
```bash
cd /mnt/c/Users/ssking1999/Desktop/藝術史資料庫/art-history-database

# 檢查是否有進程
ps aux | grep ollama-rag-proxy

# 如果沒有，啟動它
node ollama-rag-proxy.js > ollama-rag-proxy.log 2>&1 &

# 驗證
sleep 2
curl http://localhost:11435/health
```

### 問題 3: Multi-DB RAG Server 未運行

**症狀**: RAG 查詢失敗，或回答沒有來源標註

**解決方案**:
```bash
# 檢查服務
curl http://localhost:8010/health

# 如果未運行，啟動它
cd /mnt/c/Users/ssking1999/Desktop/藝術史資料庫/art-history-database
node multi-database-rag-server.js > multi-database-rag-server.log 2>&1 &

# 驗證
sleep 2
curl http://localhost:8010/health
```

### 問題 4: WSL 重啟後無法連接

**原因**: WSL2 IP 地址改變

**解決方案**:
```bash
# 使用自動化腳本
bash restart-openwebui-wsl2.sh
```

---

## 📋 完整檢查清單

在確認 RAG 功能正常工作前，請檢查：

- [ ] OpenWebUI 可訪問（http://localhost:8080）
- [ ] Ollama RAG Proxy 運行中（端口 11435）
- [ ] Multi-DB RAG Server 運行中（端口 8010）
- [ ] Ollama 運行中（端口 11434）
- [ ] Neo4j 運行中（端口 7474）
- [ ] ChromaDB 運行中（端口 8001）
- [ ] OpenWebUI 已配置 Ollama 連接（指向 11435）
- [ ] 模型下拉菜單中可見 RAG 組合模型
- [ ] 測試查詢返回正確格式的回答
- [ ] 回答包含來源標註

---

## 🔄 關於 `ollama list` 中看不到 RAG 模型的說明

### 這是正常的！

**原因**:
- `ollama list` 只顯示原生 Ollama 模型（端口 11434）
- RAG 組合模型是通過 **Ollama RAG Proxy**（端口 11435）提供的
- 它們不會出現在 `ollama list` 中

### 正確的檢查方法

**查看 RAG 組合模型**:
```bash
# 方法 1: 通過 Proxy API
curl http://localhost:11435/api/tags | grep -o '"name":"[^"]*-[^"]*_rag"'

# 方法 2: 在 OpenWebUI 界面中
# 訪問 http://localhost:8080
# 點擊模型下拉菜單
# 應該看到 24 個 RAG 組合模型
```

**查看原生 Ollama 模型**:
```bash
# 方法 1: ollama 命令
ollama list

# 方法 2: 通過 API
curl http://localhost:11434/api/tags
```

### 系統架構說明

```
OpenWebUI (8080)
    ↓
    ├─→ Ollama RAG Proxy (11435)  ← RAG 組合模型在這裡！
    │       ↓
    │       ├─→ Multi-DB RAG Server (8010)
    │       │       ↓
    │       │       ├─→ Neo4j (7474)
    │       │       └─→ ChromaDB (8001)
    │       │
    │       └─→ Real Ollama (11434)
    │               ↓
    │               └─→ 基礎 LLM 模型（llama3.1, qwen2.5, gemma2）
    │
    └─→ Real Ollama (11434)  ← 可選：直接使用原生模型
```

---

## 🎯 快速啟動腳本

為了方便，我已經創建了自動化腳本：

### 檢查所有服務

```bash
bash setup-ollama-rag-proxy.sh
```

### WSL 重啟後重新配置

```bash
bash restart-openwebui-wsl2.sh
```

---

## 📚 相關文檔

1. **ollama-rag-proxy使用指南.md** - 完整使用手冊
2. **WSL2環境配置說明.md** - WSL2 特定配置
3. **問題修復報告_OpenWebUI當機.md** - 問題診斷記錄
4. **OLLAMA_RAG_PROXY_完成報告.md** - 技術報告

---

## ✅ 總結

### 當前狀態
- ✅ OpenWebUI 已正常運行
- ✅ 無認證問題
- ✅ 全新資料庫

### 下一步
1. 驗證後端服務（步驟 1）
2. 配置 OpenWebUI 連接（步驟 2）
3. 驗證 RAG 模型（步驟 3）
4. 測試 RAG 查詢（步驟 4）

### 預期結果
- 在 OpenWebUI 中看到 24 個 RAG+LLM 組合模型
- 可以使用 RAG 模型進行藝術史查詢
- 回答包含完整的來源標註

---

**準備好了嗎？** 從步驟 1 開始，逐步添加 RAG 功能！ 🚀
