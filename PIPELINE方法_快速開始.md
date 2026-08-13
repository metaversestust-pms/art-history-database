# 🚀 OpenWebUI Pipeline 方法 - 快速開始

**5 分鐘創建 RAG+LLM 組合模型！**

---

## ✅ 準備工作

### 確認後端服務運行

```bash
# 檢查 Multi-DB RAG Server
curl http://localhost:8010/health
# 應該返回: {"status":"ok"...}

# 檢查 Ollama
curl http://localhost:11434/api/tags
# 應該返回模型列表
```

如果服務未運行：
```bash
# 啟動 Multi-DB RAG Server
cd /mnt/c/Users/ssking1999/Desktop/藝術史資料庫/art-history-database
node multi-database-rag-server.js > multi-database-rag-server.log 2>&1 &
```

---

## 📝 步驟 1: 複製 Pipeline 代碼

```bash
# 查看 Pipeline 代碼
cat art_history_rag_pipeline.py
```

**或者直接在這裡複製**：文件位於 `art_history_rag_pipeline.py`

---

## 🌐 步驟 2: 上傳到 OpenWebUI

### 2.1 訪問 OpenWebUI

打開瀏覽器：**http://localhost:8080**

### 2.2 進入 Admin Panel

1. 點擊左下角 **齒輪圖標** (Settings)
2. 找到 **"Admin Panel"** 或 **"Admin Settings"**
3. 點擊 **"Pipelines"** 或 **"Functions"**

### 2.3 創建 Pipeline

1. 點擊 **"+"** 或 **"Add Pipeline"** 按鈕
2. 在代碼編輯器中，粘貼 `art_history_rag_pipeline.py` 的內容
3. 點擊 **"Save"** 保存
4. 確認 Pipeline 狀態為 **"Active"** (綠色)

---

## 🎯 步驟 3: 創建第一個測試模型

### 3.1 訪問 Workspace

1. 點擊左側菜單的 **"Workspace"**
2. 選擇 **"Models"**

### 3.2 添加模型

點擊 **"+ Add Model"** 或 **"Create Model"**

### 3.3 填寫模型信息

**第一個測試模型配置**:
```
Name: qwen3-4b-vector_rag
Display Name: 🐲 Qwen3 4B + 🔍 VectorRAG
Base Model: 選擇 "Art History RAG Pipeline"
Description: 中文優化 + 向量語義檢索
```

點擊 **"Save"** 或 **"Create"**

---

## ✨ 步驟 4: 測試模型

### 4.1 創建新對話

1. 點擊主界面的 **"New Chat"** 或 **"+"**
2. 在模型選擇器中，找到：**🐲 Qwen3 4B + 🔍 VectorRAG**

### 4.2 發送測試問題

```
莫內的代表作品有哪些？
```

### 4.3 檢查回答

**預期回答格式**:
```
克洛德·莫內（Claude Monet）是印象派的創始人之一，他的代表作品包括：

1. 《印象·日出》（Impression, Sunrise）
2. 《睡蓮》系列
3. 《乾草堆》系列
...

---

📊 **檢索信息**
- 🔍 RAG 策略: vector_only
- 🤖 LLM 模型: qwen3:4b
- 📚 檢索來源: 5 個

**參考資料來源:**
1. 📊 CHROMADB > Met Museum API
   🎯 相關度: 0.94 | 方法: vector
2. 📊 CHROMADB > WikiArt
   🎯 相關度: 0.91 | 方法: vector
...
```

---

## 🎉 成功！下一步

如果測試成功，您可以繼續創建更多模型組合：

### 推薦的前 5 個模型

1. ✅ `qwen3-4b-vector_rag` - 已創建
2. `llama3-1-8b-basic_rag` - 🦙 Llama 3.1 8B + ⚖️ 基礎RAG
3. `gemma3-1b-naive_rag` - ⚡ Gemma3 1B + ⚡ NaiveRAG
4. `gpt-oss-20b-advanced_rag` - 🤖 GPT-OSS 20B + 🎯 Advanced RAG
5. `deepseek-r1-8b-graph_rag` - 🧠 DeepSeek-R1 8B + 🕸️ GraphRAG

每個模型的創建步驟相同，只需修改：
- **Name**: 模型 ID（如 `llama3-1-8b-basic_rag`）
- **Display Name**: 顯示名稱（加上圖標）

---

## 🐛 遇到問題？

### 問題 1: Pipeline 保存失敗

**解決方案**:
- 檢查代碼是否完整複製
- 確保沒有語法錯誤
- 嘗試刷新頁面後重新上傳

### 問題 2: 模型不顯示

**解決方案**:
- 確認 Pipeline 狀態為 "Active"
- 刷新 OpenWebUI 頁面（F5）
- 檢查瀏覽器控制台是否有錯誤

### 問題 3: 回答沒有來源標註

**解決方案**:
```bash
# 檢查 RAG Server
curl http://localhost:8010/health

# 如果未運行，啟動它
node multi-database-rag-server.js > multi-database-rag-server.log 2>&1 &
```

### 問題 4: WSL2 環境連接問題

如果您在 WSL2 環境中，可能需要修改 Pipeline 中的 URL：

在 Pipeline 代碼的 `Valves` 部分，將：
```python
RAG_SERVER_URL: str = "http://localhost:8010"
OLLAMA_BASE_URL: str = "http://localhost:11434"
```

改為（使用 WSL2 IP）：
```python
RAG_SERVER_URL: str = "http://172.26.104.197:8010"
OLLAMA_BASE_URL: str = "http://172.26.104.197:11434"
```

---

## 📚 完整文檔

- **創建OpenWebUI模型組合指南.md** - 詳細指南（包含所有 35 個模型）
- **art_history_rag_pipeline.py** - Pipeline 源代碼
- **MODEL_COMBINATIONS_LIST.md** - 模型組合清單

---

## ✅ 檢查清單

在開始使用前，請確認：

- [ ] Multi-DB RAG Server 運行中（端口 8010）
- [ ] Ollama 運行中（端口 11434）
- [ ] Pipeline 已上傳到 OpenWebUI
- [ ] Pipeline 狀態為 "Active"
- [ ] 至少創建了 1 個測試模型
- [ ] 測試模型可以正常工作
- [ ] 回答包含來源標註

**全部確認後，就可以開始使用了！** 🎨

---

**預計時間**: 5-10 分鐘
**難度**: ⭐⭐ (簡單)
**方法**: OpenWebUI Pipeline (官方推薦)
