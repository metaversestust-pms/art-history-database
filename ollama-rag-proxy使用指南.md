# 🚀 Ollama RAG Proxy 使用指南

**最新更新**: 2025-10-19
**版本**: 1.0
**狀態**: ✅ 已啟動並運行（PID: 80701）

---

## 📋 概述

Ollama RAG Proxy 是一個創新解決方案，它將 **RAG+LLM 策略包裝成標準的 Ollama 模型**。

### 為什麼使用這個方法？

✅ **無需更新 OpenWebUI Function** - 完全繞過 Function 更新的麻煩
✅ **像使用普通模型一樣簡單** - 在模型下拉菜單中直接選擇
✅ **完整的多資料庫支援** - 自動整合 Neo4j + ChromaDB
✅ **完整的來源追溯** - 清楚顯示資料來源

---

## 🎯 快速開始（3 分鐘）

### 步驟 1: 確認 Proxy 正在運行 (30 秒)

在終端執行：

```bash
curl http://localhost:11435/health
```

**預期輸出**:
```json
{
  "status": "ok",
  "service": "ollama-rag-proxy",
  "rag_server": "http://localhost:8010",
  "ollama_server": "http://localhost:11434",
  "strategies": ["vector_rag", "graph_rag", "hybrid_rag", ...]
}
```

如果沒有回應，啟動服務：
```bash
cd /mnt/c/Users/ssking1999/Desktop/藝術史資料庫/art-history-database
node ollama-rag-proxy.js > ollama-rag-proxy.log 2>&1 &
```

### 步驟 2: 在 OpenWebUI 中添加 Proxy 連接 (1 分鐘)

1. **打開 OpenWebUI**: http://localhost:8080

2. **進入設置**:
   - 點擊左下角用戶圖標或齒輪圖標
   - 選擇 **Settings** (設置)
   - 找到 **Connections** 或 **External Connections**

3. **添加 Ollama 連接**:
   ```
   名稱: RAG Proxy
   URL: http://localhost:11435
   ```

4. **保存設置**

### 步驟 3: 選擇 RAG+LLM 組合模型 (30 秒)

1. **回到聊天界面**
2. **點擊模型選擇下拉菜單**
3. **選擇任一 RAG 組合模型**，例如:
   - `llama3.1-vector_rag`
   - `qwen2.5-hybrid_rag`
   - `gemma2-graph_rag`

### 步驟 4: 開始提問！(1 分鐘)

試試這些問題：
```
莫內的代表作品有哪些？
印象派和後印象派的主要區別是什麼？
文藝復興時期的藝術特點是什麼？
```

---

## 📊 可用的 RAG+LLM 組合模型

Proxy 提供 **24 個組合模型**（3 個基礎 LLM × 8 個 RAG 策略）

### 基礎 LLM 模型

| 簡寫 | 完整模型 | 特點 |
|------|----------|------|
| `llama3.1` | llama3.1:8b | 通用性強，推理能力好 |
| `qwen2.5` | qwen2.5:7b | 中文優化，速度快 |
| `gemma2` | gemma2:2b | 輕量級，響應快 |

### RAG 策略

| 策略名稱 | 主要資料庫 | 適用場景 | 模型示例 |
|---------|-----------|---------|---------|
| `vector_rag` | ChromaDB優先 | 基於相似度的快速檢索 | `llama3.1-vector_rag` |
| `graph_rag` | Neo4j | 關係圖譜，深度探索 | `qwen2.5-graph_rag` |
| `hybrid_rag` | Neo4j+ChromaDB | 平衡型，綜合檢索 | `llama3.1-hybrid_rag` |
| `enhanced_rag` | Neo4j+ChromaDB | 增強型，多輪優化 | `qwen2.5-enhanced_rag` |
| `advanced_rag` | ChromaDB優先 | 高級語義理解 | `llama3.1-advanced_rag` |
| `agentic_rag` | ChromaDB優先 | 智能代理，自主決策 | `gemma2-agentic_rag` |
| `self_rag` | ChromaDB優先 | 自我反思，質量控制 | `llama3.1-self_rag` |
| `naive_rag` | ChromaDB | 快速檢索，簡單直接 | `qwen2.5-naive_rag` |

---

## 💡 使用示例

### 示例 1: 使用 Vector RAG 查詢藝術作品

**選擇模型**: `llama3.1-vector_rag`

**提問**: "莫內的《睡蓮》系列有什麼特點？"

**預期回應格式**:
```
莫內的《睡蓮》系列是印象派繪畫的巔峰之作，主要特點包括：

1. **光影變化**: 通過不同時間、不同光線條件下的描繪，展現水面光影的微妙變化
2. **色彩運用**: 大量使用藍色、綠色和紫色，營造寧靜氛圍
3. **筆觸技法**: 快速、短促的筆觸，捕捉瞬間印象

---

📊 **檢索信息**
- 🔍 RAG 策略: vector_rag
- 💾 資料庫: ChromaDB優先
- 🤖 LLM 模型: llama3.1:8b
- 📚 檢索來源: 3 個

**參考資料來源:**
1. 📊 CHROMADB > Met Museum API
   🎯 相關度: 0.92 | 方法: vector
2. 📊 CHROMADB > WikiArt
   🎯 相關度: 0.88 | 方法: vector
3. 📊 NEO4J > Internal Knowledge Base
   🎯 相關度: 0.85 | 方法: fulltext
```

### 示例 2: 使用 Graph RAG 探索藝術家關係

**選擇模型**: `qwen2.5-graph_rag`

**提問**: "梵高和高更的關係是什麼？"

**預期回應**: 會利用 Neo4j 知識圖譜，展示藝術家之間的關係路徑

### 示例 3: 使用 Hybrid RAG 綜合查詢

**選擇模型**: `llama3.1-hybrid_rag`

**提問**: "印象派有哪些代表藝術家和作品？"

**預期回應**: 結合 Neo4j 圖譜關係和 ChromaDB 向量檢索，提供全面答案

---

## 🔧 詳細配置說明

### OpenWebUI 連接配置位置

根據 OpenWebUI 版本，設置位置可能不同：

**方法 A: Settings → Connections**
```
1. 點擊左側菜單 ☰
2. 選擇 Settings
3. 找到 Connections 或 External Connections
4. 點擊 "+ Add Connection"
5. 填寫:
   - Name: RAG Proxy
   - Type: Ollama
   - URL: http://localhost:11435
6. 點擊 Save
```

**方法 B: Admin Settings → External Connections**
```
1. 點擊左側菜單 ☰
2. 選擇 Admin Settings
3. 找到 External Connections
4. 添加 Ollama 連接: http://localhost:11435
```

**方法 C: Models → Add Model Source**
```
1. 進入 Models 頁面
2. 點擊 "Add Model Source" 或 "+"
3. 輸入 Ollama URL: http://localhost:11435
```

### 如果找不到設置選項

如果您無法找到添加 Ollama 連接的地方，可以嘗試：

1. **修改 Docker 環境變量**（推薦）

停止 OpenWebUI 容器：
```bash
docker stop art-history-openwebui
```

重新啟動並設置 Ollama URL：
```bash
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

2. **使用多個 Ollama 連接**

如果 OpenWebUI 支援多個 Ollama 連接，您可以：
- 保留原有的 Ollama (11434) 用於普通模型
- 添加 RAG Proxy (11435) 用於 RAG 模型

---

## 📸 視覺化說明

### 系統架構

```
┌─────────────────────────────────────────────────────┐
│                   OpenWebUI (8080)                  │
│                                                     │
│  用戶選擇: llama3.1-vector_rag                       │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│           Ollama RAG Proxy (11435)                  │
│                                                     │
│  1. 解析模型名稱: llama3.1 + vector_rag              │
│  2. 路由到 RAG Server                                │
└─────────────┬─────────────────┬─────────────────────┘
              │                 │
              ▼                 ▼
┌─────────────────────┐  ┌──────────────────────────┐
│  Multi-DB RAG       │  │  Real Ollama (11434)    │
│  Server (8010)      │  │                          │
│                     │  │  生成最終回答              │
│  查詢 ChromaDB      │  └──────────────────────────┘
│  查詢 Neo4j         │
│  合併結果           │
└─────────────────────┘
```

### 數據流程

```
用戶問題: "莫內的作品有哪些？"
     ↓
Ollama Proxy 解析
     ↓
RAG 檢索 (ChromaDB + Neo4j)
     ↓
構建增強提示詞
     ↓
Ollama LLM 生成
     ↓
格式化回答 + 來源標註
     ↓
返回給用戶
```

---

## 🐛 故障排除

### 問題 1: 無法連接到 Proxy

**症狀**: OpenWebUI 顯示 "Connection failed" 或無法載入模型

**解決方案**:
```bash
# 檢查 Proxy 是否運行
curl http://localhost:11435/health

# 如果沒有回應，重新啟動
cd /mnt/c/Users/ssking1999/Desktop/藝術史資料庫/art-history-database
node ollama-rag-proxy.js > ollama-rag-proxy.log 2>&1 &

# 檢查日誌
tail -f ollama-rag-proxy.log
```

### 問題 2: 看不到 RAG 模型

**症狀**: 模型列表中只有普通模型，沒有 RAG 組合模型

**解決方案**:
```bash
# 測試 API 端點
curl http://localhost:11435/api/tags

# 應該看到 24 個 RAG 組合模型
# 例如: llama3.1-vector_rag, qwen2.5-graph_rag 等

# 如果沒有，檢查 Proxy 日誌
cat ollama-rag-proxy.log
```

### 問題 3: RAG 檢索失敗

**症狀**: 回答中顯示 "RAG 服務不可用"

**解決方案**:
```bash
# 檢查 Multi-DB RAG Server 是否運行
curl http://localhost:8010/health

# 如果沒有回應，重新啟動
node multi-database-rag-server.js > multi-db-rag.log 2>&1 &

# 檢查日誌
tail -f multi-db-rag.log
```

### 問題 4: 來源標註缺失

**症狀**: 回答沒有顯示 "📊 檢索信息" 部分

**可能原因**:
- RAG 檢索沒有返回 sources 字段
- Proxy 格式化邏輯有問題

**解決方案**:
```bash
# 手動測試 RAG 查詢
curl -X POST http://localhost:8010/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "莫內的作品",
    "strategy": "vector_only",
    "top_k": 5
  }'

# 檢查返回的 sources 字段
```

### 問題 5: Docker 容器無法訪問 Proxy

**症狀**: OpenWebUI 在 Docker 中運行，無法連接 localhost:11435

**解決方案**:

使用 `host.docker.internal` 代替 `localhost`:
```bash
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

---

## 📊 服務狀態檢查

### 快速健康檢查腳本

創建一個檢查腳本：

```bash
#!/bin/bash
echo "🔍 檢查所有服務狀態..."
echo ""

# 檢查 Ollama RAG Proxy
echo "1. Ollama RAG Proxy (11435):"
curl -s http://localhost:11435/health > /dev/null
if [ $? -eq 0 ]; then
    echo "   ✅ 運行正常"
else
    echo "   ❌ 無法連接"
fi

# 檢查 Multi-DB RAG Server
echo "2. Multi-DB RAG Server (8010):"
curl -s http://localhost:8010/health > /dev/null
if [ $? -eq 0 ]; then
    echo "   ✅ 運行正常"
else
    echo "   ❌ 無法連接"
fi

# 檢查 Real Ollama
echo "3. Real Ollama (11434):"
curl -s http://localhost:11434/api/tags > /dev/null
if [ $? -eq 0 ]; then
    echo "   ✅ 運行正常"
else
    echo "   ❌ 無法連接"
fi

# 檢查 ChromaDB
echo "4. ChromaDB (8001):"
curl -s http://localhost:8001/api/v1/heartbeat > /dev/null
if [ $? -eq 0 ]; then
    echo "   ✅ 運行正常"
else
    echo "   ❌ 無法連接"
fi

# 檢查 Neo4j
echo "5. Neo4j (7474):"
curl -s http://localhost:7474 > /dev/null
if [ $? -eq 0 ]; then
    echo "   ✅ 運行正常"
else
    echo "   ❌ 無法連接"
fi

# 檢查 OpenWebUI
echo "6. OpenWebUI (8080):"
curl -s http://localhost:8080 > /dev/null
if [ $? -eq 0 ]; then
    echo "   ✅ 運行正常"
else
    echo "   ❌ 無法連接"
fi

echo ""
echo "✅ 檢查完成！"
```

保存為 `check-rag-services.sh` 並執行：
```bash
chmod +x check-rag-services.sh
./check-rag-services.sh
```

---

## 🎓 進階使用技巧

### 技巧 1: 選擇最適合的 RAG 策略

| 問題類型 | 推薦策略 | 理由 |
|---------|---------|------|
| 查詢具體作品信息 | `vector_rag` | 基於語義相似度，快速匹配 |
| 探索藝術家關係 | `graph_rag` | 利用知識圖譜，深度挖掘 |
| 綜合性問題 | `hybrid_rag` | 結合多種檢索方法 |
| 需要多輪推理 | `enhanced_rag` | 支援多步驟查詢優化 |
| 複雜學術問題 | `agentic_rag` | 智能代理自主決策 |
| 要求高準確度 | `self_rag` | 自我反思，質量控制 |

### 技巧 2: 選擇最適合的基礎模型

| 需求 | 推薦模型 | 理由 |
|-----|---------|------|
| 中文回答質量 | `qwen2.5` | 專門優化中文 |
| 推理能力 | `llama3.1` | 強大的邏輯推理 |
| 速度優先 | `gemma2` | 輕量級，響應快 |

### 技巧 3: 理解來源標註

回答底部的來源信息可以幫您：
- **評估答案可靠性**: Met Museum API > WikiArt > Internal KB
- **追溯資料來源**: 知道資訊從哪裡來
- **理解檢索方法**: vector 是語義匹配，fulltext 是關鍵詞匹配

---

## 📚 相關文檔

- **完整項目報告**: `FINAL_PROJECT_REPORT.md`
- **系統狀態摘要**: `SYSTEM_STATUS_SUMMARY.md`
- **快速參考**: `QUICK_REFERENCE.md`
- **多資料庫架構**: `MULTI_DATABASE_ARCHITECTURE.md`
- **Function 更新說明**: `OpenWebUI_Function更新_最終說明.md`

---

## ✅ 總結

### 您已經擁有的能力

✅ **24 個 RAG+LLM 組合模型** 可供選擇
✅ **雙資料庫整合** (Neo4j + ChromaDB)
✅ **完整來源追溯** 知道每個答案的資料來源
✅ **無需更新 Function** 像使用普通模型一樣簡單

### 開始使用

1. 確認 Proxy 運行: `curl http://localhost:11435/health`
2. 在 OpenWebUI 添加連接: `http://localhost:11435`
3. 選擇 RAG 模型並開始提問！

---

**需要幫助？** 查看故障排除部分或檢查服務日誌。

**祝您使用愉快！** 🎉
