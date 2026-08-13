# 🚀 Ollama RAG Proxy - 快速開始指南

**只需 3 步，3 分鐘即可開始使用！**

---

## ✅ 當前狀態

所有服務已啟動並運行：

- ✅ Neo4j (7474)
- ✅ ChromaDB (8001)
- ✅ Ollama (11434)
- ✅ OpenWebUI (8080)
- ✅ Multi-DB RAG Server (8010)
- ✅ **Ollama RAG Proxy (11435)** ← 新增！

---

## 🎯 第 1 步: 重新配置 OpenWebUI（2 分鐘）

### 在終端執行以下命令：

```bash
# 停止現有容器
docker stop art-history-openwebui

# 刪除舊容器（不會刪除資料）
docker rm art-history-openwebui

# 重新啟動並指向 RAG Proxy
docker run -d \
  --name art-history-openwebui \
  --restart always \
  -p 8080:8080 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11435 \
  -e WEBUI_AUTH=false \
  -v open-webui:/app/backend/data \
  --add-host=host.docker.internal:host-gateway \
  ghcr.io/open-webui/open-webui:main
```

**重要說明**:
- 這個命令會將 OpenWebUI 指向端口 **11435**（RAG Proxy），而非 11434（原始 Ollama）
- 您的聊天歷史會保留（使用 Docker volume）
- 配置只需執行一次

---

## 🎯 第 2 步: 驗證配置（30 秒）

### 訪問 OpenWebUI

在瀏覽器打開: **http://localhost:8080**

### 檢查模型列表

點擊新對話中的**模型選擇下拉菜單**，您應該看到：

**RAG 組合模型**（以下是部分示例）：
```
llama3.1-vector_rag      ← ChromaDB 向量檢索
llama3.1-graph_rag       ← Neo4j 圖譜檢索
llama3.1-hybrid_rag      ← 混合檢索
llama3.1-enhanced_rag    ← 增強型檢索
qwen2.5-vector_rag       ← Qwen 中文優化 + ChromaDB
qwen2.5-graph_rag        ← Qwen + Neo4j
gemma2-advanced_rag      ← Gemma2 輕量級 + 高級檢索
... 等共 24 個組合
```

**原始 Ollama 模型**（如果您之前有安裝）：
```
llama3.1:8b
qwen2.5:7b
gemma2:2b
...
```

---

## 🎯 第 3 步: 開始提問！（30 秒）

### 選擇 RAG 模型

在模型下拉菜單中選擇任一 RAG 組合，例如：
- `llama3.1-vector_rag`（推薦新手）
- `qwen2.5-hybrid_rag`（中文優化）

### 提問示例

試試以下藝術史問題：

```
莫內的代表作品有哪些？
```

```
印象派和後印象派的主要區別是什麼？
```

```
文藝復興時期有哪些著名藝術家？
```

### 預期回答格式

您會看到：

1. **主要回答** - LLM 基於 RAG 檢索生成的回答
2. **檢索信息** - 顯示使用的 RAG 策略、資料庫、LLM 模型
3. **參考資料來源** - 列出具體的資料來源、相關度、檢索方法

示例：
```
莫內的代表作品包括《印象·日出》、《睡蓮》系列...

---

📊 **檢索信息**
- 🔍 RAG 策略: vector_rag
- 💾 資料庫: ChromaDB優先
- 🤖 LLM 模型: llama3.1:8b
- 📚 檢索來源: 5 個

**參考資料來源:**
1. 📊 CHROMADB > Met Museum API
   🎯 相關度: 0.94 | 方法: vector
2. 📊 CHROMADB > WikiArt
   🎯 相關度: 0.91 | 方法: vector
...
```

---

## 🎓 進階技巧

### 技巧 1: 根據問題選擇最佳策略

| 問題類型 | 推薦模型 |
|---------|---------|
| 查詢具體作品信息 | `llama3.1-vector_rag` |
| 探索藝術家關係 | `llama3.1-graph_rag` |
| 綜合性問題 | `qwen2.5-hybrid_rag` |
| 需要深度推理 | `llama3.1-enhanced_rag` |

### 技巧 2: 選擇基礎模型

| 需求 | 推薦基礎模型 |
|-----|-----------|
| 中文回答質量 | `qwen2.5-*` |
| 推理能力 | `llama3.1-*` |
| 速度優先 | `gemma2-*` |

---

## 🐛 故障排除

### 問題 1: 看不到 RAG 組合模型

**解決方案**:
```bash
# 檢查 OpenWebUI 的 Ollama URL 設置
docker inspect art-history-openwebui | grep OLLAMA_BASE_URL

# 應該顯示: "OLLAMA_BASE_URL=http://host.docker.internal:11435"
# 如果不是，重新執行第 1 步的命令
```

### 問題 2: RAG Proxy 沒有運行

**解決方案**:
```bash
# 檢查 Proxy 狀態
curl http://localhost:11435/health

# 如果沒有回應，重新啟動
cd /mnt/c/Users/ssking1999/Desktop/藝術史資料庫/art-history-database
node ollama-rag-proxy.js > ollama-rag-proxy.log 2>&1 &

# 等待 2 秒後再次測試
sleep 2
curl http://localhost:11435/health
```

### 問題 3: Multi-DB RAG Server 沒有運行

**解決方案**:
```bash
# 檢查 RAG Server 狀態
curl http://localhost:8010/health

# 如果沒有回應，重新啟動
cd /mnt/c/Users/ssking1999/Desktop/藝術史資料庫/art-history-database
node multi-database-rag-server.js > multi-database-rag-server.log 2>&1 &

# 等待 2 秒後再次測試
sleep 2
curl http://localhost:8010/health
```

### 問題 4: 回答沒有來源標註

**可能原因**: RAG 檢索可能失敗

**解決方案**:
```bash
# 查看 Proxy 日誌
tail -20 ollama-rag-proxy.log

# 查看 RAG Server 日誌
tail -20 multi-database-rag-server.log
```

---

## 📚 完整文檔

想了解更多？查看以下文檔：

1. **ollama-rag-proxy使用指南.md** - 完整使用手冊
2. **OLLAMA_RAG_PROXY_完成報告.md** - 完成報告
3. **setup-ollama-rag-proxy.sh** - 自動設置腳本

---

## ✅ 快速檢查清單

在開始使用前，確認以下項目：

- [ ] 已執行第 1 步重新配置 OpenWebUI
- [ ] OpenWebUI 可以訪問（http://localhost:8080）
- [ ] 模型下拉菜單中可以看到 RAG 組合模型
- [ ] 選擇了一個 RAG 模型
- [ ] 已提出第一個藝術史問題

如果所有項目都已勾選，恭喜您！系統已完全配置！

---

## 💡 快速測試命令

### 終端測試（可選）

如果您想在終端快速測試系統：

```bash
# 測試 1: 健康檢查
curl http://localhost:11435/health

# 測試 2: 查看可用模型（前 5 個 RAG 模型）
curl -s http://localhost:11435/api/tags | grep -o '"name":"llama3.1-[^"]*"' | head -5

# 測試 3: 簡單 RAG 查詢
curl -X POST http://localhost:11435/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1-vector_rag",
    "prompt": "印象派的特點",
    "stream": false
  }'
```

---

## 🎉 總結

**您現在擁有的能力**：

✅ 24 個 RAG+LLM 組合模型
✅ 雙資料庫整合（Neo4j + ChromaDB）
✅ 完整來源追溯
✅ 像使用普通模型一樣簡單

**下一步**：

開始在 OpenWebUI 中探索藝術史世界！🎨

---

**遇到問題？**

1. 查看故障排除部分
2. 查看服務日誌
3. 閱讀完整文檔

**祝您使用愉快！** 🚀
