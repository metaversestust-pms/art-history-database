# 🎨 OpenWebUI 藝術史 RAG+LLM 模型組合創建指南

**目標**: 在 OpenWebUI 中創建 35 個 LLM+RAG 組合模型
**方法**: 使用 OpenWebUI Pipeline 功能
**狀態**: ✅ 準備就緒

---

## 📋 方案概述

### 為什麼使用 Pipeline？

之前嘗試的 Ollama RAG Proxy 方法遇到問題，現在改用 **OpenWebUI Pipeline** 方法，這是官方推薦的方式：

✅ **優點**:
- 官方支持，穩定性好
- 在 OpenWebUI 界面中直接管理
- 支持流式輸出
- 易於調試和更新

❌ **Ollama Proxy 的問題**:
- API 端點不完整
- 與 OpenWebUI 兼容性問題
- 難以維護

---

## 🚀 步驟 1: 上傳 Pipeline 到 OpenWebUI

### 1.1 訪問 OpenWebUI

打開瀏覽器訪問: **http://localhost:8080**

### 1.2 進入 Pipelines 管理

1. 點擊左下角的 **設置圖標** (齒輪)
2. 在左側菜單中找到 **Admin Panel** 或 **Admin Settings**
3. 點擊 **Pipelines** (或 **Functions**)

### 1.3 創建新 Pipeline

1. 點擊 **"+ Add Pipeline"** 或 **"Create New Pipeline"** 按鈕
2. 選擇上傳方式：
   - **方法 A**: 點擊 **"Upload from File"**，選擇 `art_history_rag_pipeline.py`
   - **方法 B**: 點擊 **"Import from URL"**，輸入文件路徑
   - **方法 C**: 直接複製粘貼代碼

### 1.4 複製 Pipeline 代碼（方法 C）

如果選擇直接複製，請使用以下命令查看代碼：

```bash
cat art_history_rag_pipeline.py
```

然後將整個文件內容複製到 OpenWebUI 的代碼編輯器中。

### 1.5 保存 Pipeline

1. 點擊 **"Save"** 或 **"Create"** 按鈕
2. 確認 Pipeline 名稱顯示為：**"Art History RAG Pipeline"**
3. 檢查狀態是否為 **"Active"** 或 **"Enabled"**

---

## 🎯 步驟 2: 在 OpenWebUI 中創建模型

### 2.1 訪問模型管理

1. 在 OpenWebUI 中，點擊左側菜單的 **"Workspace"**
2. 選擇 **"Models"** 或 **"模型"**
3. 點擊 **"+ Add Model"** 或類似按鈕

### 2.2 創建第一個測試模型

**模型配置**:
- **Name**: `qwen3-4b-vector_rag`
- **Display Name**: `🐲 Qwen3 4B + 🔍 VectorRAG`
- **Pipeline**: 選擇 **"Art History RAG Pipeline"**
- **Description**: 中文優化 + 向量語義檢索

點擊 **"Save"** 保存。

### 2.3 測試模型

1. 回到主界面，點擊 **"New Chat"**
2. 在模型選擇器中，應該看到剛創建的模型：`🐲 Qwen3 4B + 🔍 VectorRAG`
3. 發送測試問題：
   ```
   莫內的代表作品有哪些？
   ```
4. 檢查回答是否包含：
   - ✅ 主要回答內容
   - ✅ 檢索信息
   - ✅ 參考資料來源

---

## 📊 步驟 3: 批量創建所有 35 個模型

### 模型清單（按優先級）

#### 🌟 優先創建（最常用的 10 個）

1. `qwen3-4b-vector_rag` - 🐲 Qwen3 4B + 🔍 VectorRAG
2. `qwen3-4b-basic_rag` - 🐲 Qwen3 4B + ⚖️ 基礎RAG
3. `llama3-1-8b-vector_rag` - 🦙 Llama 3.1 8B + 🔍 VectorRAG
4. `llama3-1-8b-basic_rag` - 🦙 Llama 3.1 8B + ⚖️ 基礎RAG
5. `gpt-oss-20b-advanced_rag` - 🤖 GPT-OSS 20B + 🎯 Advanced RAG
6. `gpt-oss-20b-graph_rag` - 🤖 GPT-OSS 20B + 🕸️ GraphRAG
7. `deepseek-r1-8b-self_rag` - 🧠 DeepSeek-R1 8B + 🔄 SelfRAG
8. `gemma3-1b-naive_rag` - ⚡ Gemma3 1B + ⚡ NaiveRAG
9. `qwen3-4b-graph_rag` - 🐲 Qwen3 4B + 🕸️ GraphRAG
10. `llama3-1-8b-agentic_rag` - 🦙 Llama 3.1 8B + 🤖 AgenticRAG

#### 📝 完整清單（35 個）

**GPT-OSS 20B 系列（7 個）**:
1. `gpt-oss-20b-basic_rag` - 🤖 GPT-OSS 20B + ⚖️ 基礎RAG
2. `gpt-oss-20b-advanced_rag` - 🤖 GPT-OSS 20B + 🎯 Advanced RAG
3. `gpt-oss-20b-vector_rag` - 🤖 GPT-OSS 20B + 🔍 VectorRAG
4. `gpt-oss-20b-graph_rag` - 🤖 GPT-OSS 20B + 🕸️ GraphRAG
5. `gpt-oss-20b-agentic_rag` - 🤖 GPT-OSS 20B + 🤖 AgenticRAG
6. `gpt-oss-20b-self_rag` - 🤖 GPT-OSS 20B + 🔄 SelfRAG
7. `gpt-oss-20b-naive_rag` - 🤖 GPT-OSS 20B + ⚡ NaiveRAG

**DeepSeek-R1 8B 系列（7 個）**:
8. `deepseek-r1-8b-basic_rag` - 🧠 DeepSeek-R1 8B + ⚖️ 基礎RAG
9. `deepseek-r1-8b-advanced_rag` - 🧠 DeepSeek-R1 8B + 🎯 Advanced RAG
10. `deepseek-r1-8b-vector_rag` - 🧠 DeepSeek-R1 8B + 🔍 VectorRAG
11. `deepseek-r1-8b-graph_rag` - 🧠 DeepSeek-R1 8B + 🕸️ GraphRAG
12. `deepseek-r1-8b-agentic_rag` - 🧠 DeepSeek-R1 8B + 🤖 AgenticRAG
13. `deepseek-r1-8b-self_rag` - 🧠 DeepSeek-R1 8B + 🔄 SelfRAG
14. `deepseek-r1-8b-naive_rag` - 🧠 DeepSeek-R1 8B + ⚡ NaiveRAG

**Gemma3 1B 系列（7 個）**:
15. `gemma3-1b-basic_rag` - ⚡ Gemma3 1B + ⚖️ 基礎RAG
16. `gemma3-1b-advanced_rag` - ⚡ Gemma3 1B + 🎯 Advanced RAG
17. `gemma3-1b-vector_rag` - ⚡ Gemma3 1B + 🔍 VectorRAG
18. `gemma3-1b-graph_rag` - ⚡ Gemma3 1B + 🕸️ GraphRAG
19. `gemma3-1b-agentic_rag` - ⚡ Gemma3 1B + 🤖 AgenticRAG
20. `gemma3-1b-self_rag` - ⚡ Gemma3 1B + 🔄 SelfRAG
21. `gemma3-1b-naive_rag` - ⚡ Gemma3 1B + ⚡ NaiveRAG

**Qwen3 4B 系列（7 個）**:
22. `qwen3-4b-basic_rag` - 🐲 Qwen3 4B + ⚖️ 基礎RAG
23. `qwen3-4b-advanced_rag` - 🐲 Qwen3 4B + 🎯 Advanced RAG
24. `qwen3-4b-vector_rag` - 🐲 Qwen3 4B + 🔍 VectorRAG
25. `qwen3-4b-graph_rag` - 🐲 Qwen3 4B + 🕸️ GraphRAG
26. `qwen3-4b-agentic_rag` - 🐲 Qwen3 4B + 🤖 AgenticRAG
27. `qwen3-4b-self_rag` - 🐲 Qwen3 4B + 🔄 SelfRAG
28. `qwen3-4b-naive_rag` - 🐲 Qwen3 4B + ⚡ NaiveRAG

**Llama 3.1 8B 系列（7 個）**:
29. `llama3-1-8b-basic_rag` - 🦙 Llama 3.1 8B + ⚖️ 基礎RAG
30. `llama3-1-8b-advanced_rag` - 🦙 Llama 3.1 8B + 🎯 Advanced RAG
31. `llama3-1-8b-vector_rag` - 🦙 Llama 3.1 8B + 🔍 VectorRAG
32. `llama3-1-8b-graph_rag` - 🦙 Llama 3.1 8B + 🕸️ GraphRAG
33. `llama3-1-8b-agentic_rag` - 🦙 Llama 3.1 8B + 🤖 AgenticRAG
34. `llama3-1-8b-self_rag` - 🦙 Llama 3.1 8B + 🔄 SelfRAG
35. `llama3-1-8b-naive_rag` - 🦙 Llama 3.1 8B + ⚡ NaiveRAG

---

## 🔧 步驟 4: Pipeline 配置

### 4.1 檢查 Pipeline 設置

在 Pipeline 管理界面中，點擊 **"Art History RAG Pipeline"** 旁的設置按鈕。

### 4.2 配置 Valves（可選）

如果需要修改配置，可以調整以下值：

```python
RAG_SERVER_URL: "http://localhost:8010"  # Multi-DB RAG Server 地址
OLLAMA_BASE_URL: "http://localhost:11434"  # Ollama 地址
ENABLE_SOURCE_ATTRIBUTION: True  # 是否顯示來源標註
MAX_SOURCES: 3  # 顯示的最大來源數量
```

**WSL2 用戶注意**: 如果 Ollama 和 RAG Server 在 WSL2 環境中，可能需要使用 WSL2 IP 地址。

---

## ✅ 步驟 5: 驗證系統

### 5.1 檢查後端服務

```bash
# 檢查所有服務狀態
curl http://localhost:8010/health  # Multi-DB RAG Server
curl http://localhost:11434/api/tags  # Ollama
```

### 5.2 測試模型

選擇剛創建的模型，發送測試問題：

```
莫內的代表作品有哪些？
```

**預期回答格式**:
```
克洛德·莫內（Claude Monet）是印象派的創始人之一...

[主要回答內容]

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

## 🐛 故障排除

### 問題 1: Pipeline 上傳失敗

**症狀**: 無法保存 Pipeline

**解決方案**:
1. 檢查 Python 語法是否正確
2. 確保所有必要的 import 都存在
3. 嘗試重新啟動 OpenWebUI

### 問題 2: 模型無法選擇

**症狀**: 創建的模型不顯示在模型列表中

**解決方案**:
1. 確認 Pipeline 已啟用（Status: Active）
2. 刷新 OpenWebUI 頁面（F5）
3. 檢查模型名稱格式是否正確

### 問題 3: RAG 檢索失敗

**症狀**: 回答中沒有來源標註

**解決方案**:
```bash
# 檢查 Multi-DB RAG Server
curl http://localhost:8010/health

# 如果未運行，啟動它
node multi-database-rag-server.js > multi-database-rag-server.log 2>&1 &
```

### 問題 4: LLM 生成失敗

**症狀**: 顯示錯誤訊息

**解決方案**:
```bash
# 檢查 Ollama
curl http://localhost:11434/api/tags

# 確認所需的模型已下載
ollama list | grep -E "(gpt-oss|deepseek|gemma|qwen|llama)"
```

---

## 📊 性能優化建議

### 優先級順序

**階段 1: 核心模型**（先創建這 5 個）
1. `qwen3-4b-vector_rag` - 中文優化，最常用
2. `llama3-1-8b-basic_rag` - 通用場景
3. `gemma3-1b-naive_rag` - 快速響應
4. `gpt-oss-20b-advanced_rag` - 高質量分析
5. `deepseek-r1-8b-self_rag` - 高準確性

**階段 2: 擴展模型**（再創建這 10 個）
- 所有 `vector_rag` 變體
- 所有 `graph_rag` 變體

**階段 3: 完整覆蓋**（最後創建剩餘的 20 個）
- 所有其他 RAG 策略組合

---

## 🎯 使用建議

### 按場景選擇模型

| 場景 | 推薦模型 |
|------|---------|
| 中文問答 | `qwen3-4b-vector_rag` |
| 快速查詢 | `gemma3-1b-naive_rag` |
| 深度分析 | `gpt-oss-20b-advanced_rag` |
| 關係探索 | `llama3-1-8b-graph_rag` |
| 高準確性 | `deepseek-r1-8b-self_rag` |

---

## 📚 相關文檔

1. **創建OpenWebUI模型組合指南.md** - 本文件
2. **art_history_rag_pipeline.py** - Pipeline 代碼
3. **MODEL_COMBINATIONS_LIST.md** - 完整模型清單
4. **RAG功能整合完成報告.md** - 系統說明

---

## ✅ 完成檢查清單

開始使用前，請確認：

- [ ] Multi-DB RAG Server 運行中（端口 8010）
- [ ] Ollama 運行中（端口 11434）
- [ ] Pipeline 已上傳並啟用
- [ ] 至少創建了 1 個測試模型
- [ ] 測試模型可以正常回答問題
- [ ] 回答包含來源標註

**如果所有項目都已確認，可以開始批量創建模型了！** 🚀

---

**最後更新**: 2025-10-20
**版本**: v1.0
**維護者**: Art History Database Team
