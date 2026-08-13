# 🎨 藝術史RAG+LLM完整組合系統部署指南

## 📋 系統概述

本系統提供 **5種LLM模型 × 6種RAG策略 = 30種組合**，為OpenWebUI創建完整的藝術史智能助手生態系統。

### 🤖 支援的LLM模型
1. **GPT-OSS 20B** - 開源GPT模型，強大語言理解
2. **DeepSeek-R1 8B** - 專注推理，邏輯思維優秀
3. **Gemma3 1B** - 輕量級，快速響應
4. **Qwen3 4B** - 中文優化，平衡性能
5. **Llama 3.1 8B** - 通用能力，指令遵循

### 🔍 支援的RAG策略
1. **⚖️ 基礎RAG** (hybrid_balanced) - 平衡混合策略
2. **🎯 Advanced RAG** (advanced_rag) - 多級檢索與重排序
3. **🔍 VectorRAG** (vector_only) - 純向量語義檢索
4. **🕸️ GraphRAG** (graph_only) - 知識圖譜關係檢索
5. **🤖 AgenticRAG** (agentic_rag) - 智能代理式推理
6. **🔄 SelfRAG** (self_rag) - 自我反思迭代改進

## 🚀 部署步驟

### 第一步：確保後端服務運行

1. **啟動統一RAG管理API**
```bash
cd art-history-database/langchain-rag
python3 unified_rag_manager.py
```
服務將在 `http://localhost:8007` 運行

2. **啟動OpenWebUI整合服務**
```bash
cd art-history-database
python3 openwebui_integration.py
```
服務將在 `http://localhost:8009` 運行

### 第二步：配置OpenWebUI函數

1. **複製增強版函數**
   - 將 `enhanced_openwebui_rag_function_v3.py` 複製到你的OpenWebUI函數目錄

2. **在OpenWebUI中安裝函數**
   - 打開OpenWebUI管理面板
   - 進入 "Functions" 設定
   - 上傳 `enhanced_openwebui_rag_function_v3.py`
   - 啟用該函數

### 第三步：創建模型組合

由於OpenWebUI的模型系統，你需要為每個組合創建對應的"模型"。以下是兩種方法：

#### 方法一：手動創建（推薦少量測試）

在OpenWebUI的模型設定中，為每個組合創建自定義模型：

**模型名稱格式**: `{llm-model}-{rag-strategy}`

例如：
- `llama3-1-8b-basic_rag`
- `qwen3-4b-advanced_rag`
- `gpt-oss-20b-agentic_rag`

#### 方法二：使用註冊腳本（推薦批量部署）

```bash
# 使用提供的註冊腳本
python3 register_openwebui_models_complete.py
```

### 第四步：驗證部署

1. **檢查後端服務**
```bash
# 測試RAG管理API
curl http://localhost:8007/health

# 測試OpenWebUI整合
curl http://localhost:8009/health
```

2. **測試模型組合**
在OpenWebUI中選擇任一組合模型，提問：
```
達文西有哪些著名的藝術作品？
```

## 🎯 使用指南

### 選擇合適的組合

#### 根據查詢類型選擇
- **事實性問答**: VectorRAG 或 基礎RAG
- **複雜分析**: Advanced RAG 或 AgenticRAG
- **關係探索**: GraphRAG
- **高準確性需求**: SelfRAG

#### 根據性能需求選擇
- **快速響應**: Gemma3 1B + VectorRAG
- **平衡性能**: Qwen3 4B + 基礎RAG
- **最佳質量**: GPT-OSS 20B + AgenticRAG
- **推理任務**: DeepSeek-R1 8B + GraphRAG
- **通用場景**: Llama 3.1 8B + Advanced RAG

### 預期響應格式

每個組合都會提供：
1. **專業回答** - 基於RAG檢索的準確答案
2. **執行信息** - 模型和策略詳情
3. **參考資料** - 檢索到的相關來源
4. **策略特色** - 所用策略的特殊說明

## 🔧 故障排除

### 常見問題

1. **服務無法連接**
   - 確認端口8007和8009未被佔用
   - 檢查防火牆設定
   - 確認相關Python依賴已安裝

2. **模型組合不顯示**
   - 確認OpenWebUI函數已正確安裝並啟用
   - 檢查函數中的API連接設定
   - 重啟OpenWebUI服務

3. **RAG檢索失敗**
   - 確認Neo4j資料庫運行正常
   - 檢查向量資料庫狀態
   - 驗證資料導入完成

### 日誌檢查

```bash
# 檢查RAG管理API日誌
tail -f art-history-database/langchain-rag/logs/rag_manager.log

# 檢查OpenWebUI整合日誌
tail -f art-history-database/logs/openwebui_integration.log
```

## 📊 性能監控

### 監控指標

系統提供以下監控信息：
- 查詢響應時間
- RAG策略使用統計
- 模型組合熱度
- 系統負載狀況

### 性能優化建議

1. **調整快取設定**
   - 增加快取大小以提高響應速度
   - 設定合適的快取TTL

2. **負載均衡**
   - 為高流量環境配置多個RAG服務實例
   - 使用反向代理分散負載

3. **資源監控**
   - 監控GPU/CPU使用率
   - 適時調整並發數設定

## 🔄 升級和維護

### 定期維護

1. **更新模型**
   - 定期檢查新版本模型
   - 測試新模型的兼容性

2. **優化策略**
   - 基於使用統計調整策略權重
   - 新增或修改RAG策略

3. **資料更新**
   - 定期更新藝術史知識庫
   - 重建向量索引和知識圖譜

### 版本控制

- 保持所有組件版本記錄
- 建立回滾機制
- 定期備份配置和資料

## 📞 技術支援

如遇問題，請提供：
1. 錯誤訊息和日誌
2. 使用的模型組合
3. 系統環境信息
4. 重現步驟

---

**🎉 恭喜！您現在擁有了一個功能完整的藝術史RAG+LLM組合系統！**