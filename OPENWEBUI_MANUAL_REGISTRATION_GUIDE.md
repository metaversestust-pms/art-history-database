# 📱 OpenWebUI手動註冊指南

## 🎯 目標
在OpenWebUI中手動註冊RAG+LLM組合模型，使用戶可以直接選擇使用。

## 📋 註冊準備

### 第一步：確保函數已上傳
1. 確認 `enhanced_openwebui_rag_function_v3.py` 已上傳到OpenWebUI
2. 確認函數處於啟用狀態
3. 確認RAG服務運行在端口8008

### 第二步：準備註冊清單

## 🏆 優先級模型清單 (推薦先註冊8種)

以下模型按優先級排序，建議首先註冊：

### 1. qwen3-4b-basic_rag
- **顯示名稱**: `🐲⚖️ Qwen3 4B + 基礎RAG`
- **描述**: `中文優化模型配合平衡混合策略，適合中文藝術史查詢，平衡性能與準確性`
- **標籤**: `中文優化, 平衡性能, 通用問答, 基礎檢索`

### 2. gpt-oss-20b-agentic_rag
- **顯示名稱**: `🤖🤖 GPT-OSS 20B + AgenticRAG`
- **描述**: `最強大的語言模型配合智能代理推理，提供多步驟分析和自主決策能力`
- **標籤**: `高性能, 複雜推理, 多步分析, 智能決策`

### 3. gemma3-1b-naive_rag
- **顯示名稱**: `⚡⚡ Gemma3 1B + NaiveRAG`
- **描述**: `極速響應組合，毫秒級處理簡單查詢，資源效率最佳`
- **標籤**: `極速響應, 資源效率, 簡單問答, 基礎匹配`

### 4. deepseek-r1-8b-self_rag
- **顯示名稱**: `🧠🔄 DeepSeek-R1 8B + SelfRAG`
- **描述**: `專注推理模型配合自我反思策略，確保高準確性和質量保證`
- **標籤**: `邏輯推理, 質量保證, 自我改進, 準確性驗證`

### 5. llama3-1-8b-graph_rag
- **顯示名稱**: `🦙🕸️ Llama 3.1 8B + GraphRAG`
- **描述**: `通用能力模型配合知識圖譜檢索，探索藝術概念間的深層關係`
- **標籤**: `通用能力, 關係分析, 結構化查詢, 概念探索`

### 6. qwen3-4b-vector_rag
- **顯示名稱**: `🐲🔍 Qwen3 4B + VectorRAG`
- **描述**: `中文優化模型配合純向量檢索，基於語義相似度的精確搜索`
- **標籤**: `中文理解, 語義搜索, 內容匹配, 相似內容`

### 7. gpt-oss-20b-advanced_rag
- **顯示名稱**: `🤖🎯 GPT-OSS 20B + Advanced RAG`
- **描述**: `強大語言模型配合多級檢索重排序，提供最深度的分析能力`
- **標籤**: `創意寫作, 複雜分析, 深度研究, 學術查詢`

### 8. gemma3-1b-basic_rag
- **顯示名稱**: `⚡⚖️ Gemma3 1B + 基礎RAG`
- **描述**: `輕量級模型配合平衡策略，快速且穩定的通用查詢處理`
- **標籤**: `快速響應, 通用問答, 平衡查詢, 資源效率`

## 🔧 OpenWebUI註冊步驟

### 方法一：通過UI界面註冊

#### 步驟1：進入模型管理
1. 打開OpenWebUI管理界面
2. 進入 **"Settings"** → **"Models"** 或 **"Admin"** → **"Models"**
3. 點擊 **"Add Model"** 或 **"+"** 按鈕

#### 步驟2：填寫模型信息
對於每個模型，按以下格式填寫：

**基本信息**：
- **Model ID**: 使用上述列表中的模型ID（如 `qwen3-4b-basic_rag`）
- **Model Name**: 使用上述列表中的顯示名稱
- **Description**: 使用上述列表中的描述
- **Tags**: 使用上述列表中的標籤（用逗號分隔）

**高級配置** (如果有)：
- **Base Model**: 選擇對應的基礎LLM模型
- **Model Type**: 選擇 "Chat"
- **Capabilities**: 選擇 "Chat"

#### 步驟3：保存和測試
1. 點擊 **"Save"** 保存模型
2. 在聊天界面測試模型是否正常工作

### 方法二：通過Ollama命令行 (如果使用Ollama)

為每個組合創建Modelfile並註冊：

```bash
# 示例：註冊 qwen3-4b-basic_rag
cat > qwen3-4b-basic_rag.Modelfile << 'EOF'
FROM qwen3:4b

PARAMETER temperature 0.7
PARAMETER top_p 0.9

SYSTEM """你是一個專業的藝術史智能助手，使用基礎RAG策略。
中文優化模型配合平衡混合策略，適合中文藝術史查詢。"""

LABEL "art-history" "true"
LABEL "rag-strategy" "basic_rag"
LABEL "llm-model" "qwen3:4b"
EOF

# 創建模型
ollama create qwen3-4b-basic_rag -f qwen3-4b-basic_rag.Modelfile
```

## 🧪 測試註冊結果

### 測試1：模型可見性
在OpenWebUI聊天界面：
1. 點擊模型選擇下拉菜單
2. 確認新註冊的模型出現在列表中
3. 模型名稱和圖標顯示正確

### 測試2：功能性測試
選擇每個模型進行測試：

**qwen3-4b-basic_rag 測試**：
```
查詢：印象派的主要特徵是什麼？
預期：正常回答 + 顯示執行信息（LLM模型、RAG策略、處理時間等）
```

**gpt-oss-20b-agentic_rag 測試**：
```
查詢：分析達文西的科學研究如何影響他的藝術創作風格
預期：顯示智能推理過程 + 多步驟分析結果
```

**gemma3-1b-naive_rag 測試**：
```
查詢：梵谷
預期：快速簡單回答（< 0.1秒）+ 極速響應說明
```

### 測試3：錯誤處理
測試錯誤情況：
1. 輸入空查詢
2. 輸入非常長的查詢
3. 在RAG服務離線時使用

## 📊 註冊追蹤表

使用以下表格追蹤註冊進度：

| 模型ID | 顯示名稱 | 註冊狀態 | 測試狀態 | 備註 |
|--------|----------|----------|----------|------|
| qwen3-4b-basic_rag | 🐲⚖️ Qwen3 4B + 基礎RAG | ⬜ | ⬜ | 最高優先級 |
| gpt-oss-20b-agentic_rag | 🤖🤖 GPT-OSS 20B + AgenticRAG | ⬜ | ⬜ | 最強分析 |
| gemma3-1b-naive_rag | ⚡⚡ Gemma3 1B + NaiveRAG | ⬜ | ⬜ | 極速響應 |
| deepseek-r1-8b-self_rag | 🧠🔄 DeepSeek-R1 8B + SelfRAG | ⬜ | ⬜ | 高準確性 |
| llama3-1-8b-graph_rag | 🦙🕸️ Llama 3.1 8B + GraphRAG | ⬜ | ⬜ | 關係分析 |
| qwen3-4b-vector_rag | 🐲🔍 Qwen3 4B + VectorRAG | ⬜ | ⬜ | 語義搜索 |
| gpt-oss-20b-advanced_rag | 🤖🎯 GPT-OSS 20B + Advanced RAG | ⬜ | ⬜ | 深度分析 |
| gemma3-1b-basic_rag | ⚡⚖️ Gemma3 1B + 基礎RAG | ⬜ | ⬜ | 快速通用 |

註冊完成後，將 ⬜ 改為 ✅

## 🔍 故障排除

### 問題1：模型不出現在列表中
**解決方案**：
1. 檢查模型ID是否正確
2. 重啟OpenWebUI服務
3. 清除瀏覽器快取

### 問題2：選擇模型後無響應
**解決方案**：
1. 檢查RAG服務(端口8008)是否運行
2. 檢查OpenWebUI函數是否啟用
3. 查看瀏覽器開發者工具的錯誤信息

### 問題3：回答格式不正確
**解決方案**：
1. 確認使用的是 `enhanced_openwebui_rag_function_v3.py`
2. 檢查函數中的API連接配置
3. 測試直接調用RAG API確認正常

## 📈 完整部署清單

完成優先級模型註冊後，可參考 `MODEL_COMBINATIONS_LIST.md` 註冊剩餘的27種組合：

- **DeepSeek-R1 8B** 組合 (6種額外)
- **Gemma3 1B** 組合 (5種額外)
- **Qwen3 4B** 組合 (5種額外)
- **Llama 3.1 8B** 組合 (6種額外)
- **GPT-OSS 20B** 組合 (5種額外)

## 🎉 註冊完成

完成優先級模型註冊後：

1. ✅ **測試核心功能** - 確保每種組合都能正常工作
2. ✅ **收集用戶反饋** - 了解哪些組合最受歡迎
3. ✅ **監控使用情況** - 通過RAG API查看使用統計
4. ✅ **逐步擴展** - 根據需求註冊更多組合

**恭喜！您現在擁有了功能完整的藝術史RAG+LLM組合系統界面！** 🎨✨