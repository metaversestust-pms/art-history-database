# 🚀 藝術史RAG+LLM組合系統最終部署指南

## 📋 部署概述

本指南將協助您將 **35種RAG+LLM組合** 完整部署到OpenWebUI，包含5種LLM模型和7種RAG策略的所有組合。

### 🎯 部署目標
- ✅ 35種完整模型組合
- ✅ 智能代理RAG (AgenticRAG)
- ✅ 極速響應RAG (NaiveRAG)
- ✅ 多級檢索和自我反思策略
- ✅ 完整的錯誤處理和監控

## 📚 文件結構

確保您有以下關鍵文件：
```
art-history-database/
├── enhanced_openwebui_rag_function_v3.py    # OpenWebUI函數 (主要)
├── langchain-rag/
│   ├── integrated_rag_optimizer.py          # RAG核心邏輯
│   └── unified_rag_manager.py               # API管理服務
├── MODEL_COMBINATIONS_LIST.md               # 組合清單
├── DEPLOYMENT_GUIDE_FINAL.md               # 本指南
└── OPENWEBUI_SETUP_GUIDE.md                # 原始設置指南
```

## 🔧 第一步：後端服務部署

### 1.1 啟動更新的RAG管理API

```bash
# 進入RAG目錄
cd art-history-database/langchain-rag

# 啟動新的RAG管理服務 (端口8008)
python3 -c "
import uvicorn
from unified_rag_manager import app
print('🚀 啟動更新後的藝術史RAG統一管理API在端口8008...')
print('📚 API文檔: http://localhost:8008/docs')
uvicorn.run(app, host='0.0.0.0', port=8008, log_level='info')
"
```

### 1.2 驗證新策略載入

```bash
# 測試策略列表
curl http://localhost:8008/system/strategies

# 預期應該看到9種策略，包含新增的：
# - agentic_rag (智能代理)
# - naive_rag (極速響應)
```

### 1.3 測試新策略功能

```bash
# 測試AgenticRAG
curl -X POST "http://localhost:8008/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "達文西的藝術技法有什麼特色？",
    "strategy": "agentic_rag",
    "top_k": 3
  }'

# 測試NaiveRAG
curl -X POST "http://localhost:8008/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "梵谷",
    "strategy": "naive_rag",
    "top_k": 3
  }'
```

## 📱 第二步：OpenWebUI函數部署

### 2.1 上傳增強版函數

1. **進入OpenWebUI管理介面**
   - 訪問您的OpenWebUI實例
   - 進入 **"Settings"** → **"Functions"**

2. **刪除舊版本函數** (如果存在)
   - 移除任何舊的藝術史RAG函數

3. **上傳新函數**
   - 上傳 `enhanced_openwebui_rag_function_v3.py`
   - 確保函數啟用狀態為 "Enabled"

### 2.2 驗證函數配置

函數應該自動檢測環境並選擇正確的API端點：
- **本地測試**: `http://localhost:8008`
- **Docker環境**: `http://host.docker.internal:8008`

## 🎨 第三步：模型組合註冊

### 3.1 理解模型命名規則

所有35種組合遵循統一命名格式：
```
{llm-model}-{rag-strategy}
```

示例：
- `gpt-oss-20b-agentic_rag` - GPT-OSS + 智能代理RAG
- `qwen3-4b-naive_rag` - Qwen3 + 極速RAG
- `llama3-1-8b-graph_rag` - Llama3.1 + 知識圖譜RAG

### 3.2 方法一：手動註冊 (推薦少量測試)

在OpenWebUI的模型管理中，創建自定義模型：

**高優先級組合** (建議優先註冊)：
1. `qwen3-4b-basic_rag` - 中文場景最佳平衡
2. `gpt-oss-20b-agentic_rag` - 最強智能分析
3. `gemma3-1b-naive_rag` - 極速響應
4. `deepseek-r1-8b-self_rag` - 高準確推理
5. `llama3-1-8b-graph_rag` - 關係分析

**每個模型配置**：
- **Model Name**: 使用上述命名格式
- **Base Model**: 選擇對應的基礎LLM模型
- **Description**: 參考 `MODEL_COMBINATIONS_LIST.md` 中的描述

### 3.3 方法二：批量註冊 (待開發)

```bash
# 使用註冊工具 (如果可用)
python3 register_openwebui_models_complete.py
```

## 🧪 第四步：測試部署

### 4.1 功能性測試

在OpenWebUI中測試不同組合：

**基礎功能測試**：
```
模型: qwen3-4b-basic_rag
查詢: "印象派的主要特徵是什麼？"
預期: 正常回答 + 執行信息顯示
```

**智能代理測試**：
```
模型: gpt-oss-20b-agentic_rag
查詢: "分析達文西的科學研究如何影響他的藝術創作"
預期: 顯示智能推理過程 + 多步分析結果
```

**極速響應測試**：
```
模型: gemma3-1b-naive_rag
查詢: "畢卡索"
預期: 快速簡單回答 (< 0.1秒)
```

### 4.2 性能驗證

檢查每個組合的響應時間：
- **極速級** (< 0.1秒): naive_rag 組合
- **快速級** (0.1-0.3秒): vector_rag 組合
- **平衡級** (0.3-0.5秒): basic_rag 組合
- **高質量級** (0.5-1.0秒): advanced_rag, self_rag 組合
- **專業級** (0.8-1.5秒): agentic_rag 組合

### 4.3 錯誤處理測試

測試各種異常情況：
1. **無效查詢**: 空白輸入
2. **服務離線**: 停止RAG服務後測試
3. **無效組合**: 使用不存在的組合名稱

## 📊 第五步：監控和優化

### 5.1 監控指標

通過管理API監控系統狀態：
```bash
# 系統狀態
curl http://localhost:8008/system/status

# 性能指標
curl http://localhost:8008/system/performance

# 快取統計
curl http://localhost:8008/system/cache
```

### 5.2 性能優化

根據使用情況調整配置：

**快取優化**：
```bash
# 調整快取大小 (預設1000)
curl -X PUT "http://localhost:8008/system/config" \
  -H "Content-Type: application/json" \
  -d '{"cache_max_size": 2000}'
```

**權重調整**：
```bash
# 調整向量/圖譜權重平衡
curl -X PUT "http://localhost:8008/system/config" \
  -H "Content-Type: application/json" \
  -d '{"vector_weight": 0.6, "graph_weight": 0.4}'
```

## 🔒 第六步：生產環境配置

### 6.1 環境變數設置

```bash
# Docker環境標識
export DOCKER_ENV=true  # Docker環境
export DOCKER_ENV=false # 本地環境

# 可選：自定義端口
export RAG_API_PORT=8008
export OPENWEBUI_PORT=8080
```

### 6.2 安全性配置

1. **API訪問限制**
   - 配置防火牆規則
   - 限制內部網路訪問

2. **資料保護**
   - 定期備份知識庫
   - 監控查詢日誌

3. **資源監控**
   - CPU/記憶體使用率
   - 磁碟空間監控

## 🆘 故障排除

### 常見問題解決

**問題1**: 組合無法識別
```bash
# 檢查組合命名是否正確
# 確認函數已正確載入
# 重啟OpenWebUI服務
```

**問題2**: RAG服務連接失敗
```bash
# 檢查端口8008是否啟用
netstat -an | grep 8008

# 檢查防火牆設置
# 確認API服務正常運行
```

**問題3**: 新策略不可用
```bash
# 確認RAG服務已重啟
# 檢查策略列表API
curl http://localhost:8008/system/strategies
```

**問題4**: 響應時間過長
```bash
# 檢查系統負載
# 調整並發數設置
# 清理快取
curl -X DELETE http://localhost:8008/system/cache
```

## 📈 使用建議

### 組合選擇指南

**日常使用**：
- 中文查詢：`qwen3-4b-basic_rag`
- 英文查詢：`llama3-1-8b-basic_rag`
- 快速查詢：`gemma3-1b-naive_rag`

**專業研究**：
- 深度分析：`gpt-oss-20b-agentic_rag`
- 關係探索：`gpt-oss-20b-graph_rag`
- 高準確性：`deepseek-r1-8b-self_rag`

**特殊場景**：
- 資源受限：`gemma3-1b-*` 系列
- 推理密集：`deepseek-r1-8b-*` 系列
- 創意寫作：`gpt-oss-20b-*` 系列

## 🎉 部署完成

恭喜！您現在擁有一個功能完整的藝術史RAG+LLM組合系統，包含：

✅ **35種智能組合** - 涵蓋所有使用場景
✅ **智能代理能力** - AgenticRAG多步推理
✅ **極速響應能力** - NaiveRAG毫秒級回答
✅ **完整監控體系** - 性能指標和狀態監控
✅ **靈活配置選項** - 支援不同環境和需求

### 下一步建議

1. **用戶培訓** - 教導用戶如何選擇最適合的組合
2. **使用分析** - 收集使用統計來優化推薦
3. **持續優化** - 根據反饋調整策略權重
4. **擴展功能** - 考慮添加更多LLM模型或RAG策略

---

**📞 技術支援**: 如有問題，請參考 `MODEL_COMBINATIONS_LIST.md` 中的詳細技術信息
**📅 最後更新**: 2025-09-28
**🔖 版本**: Final v1.0