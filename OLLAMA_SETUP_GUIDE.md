# 🦙 Ollama 本地 AI 模型整合指南

## 概述

本系統已整合 Ollama 本地 AI 模型，可完全替代 OpenAI 和 HuggingFace API，提供：
- 🔒 **隱私保護** - 所有 AI 處理在本地進行
- 💰 **零成本** - 無需 API 付費
- ⚡ **高效能** - 本地處理減少網路延遲
- 🎯 **專業化** - 針對藝術史領域最佳化

## 🚀 快速開始

### 1. 安裝 Ollama

**Windows:**
```powershell
# 下載並安裝 Ollama
# https://ollama.ai/download
# 或使用 Chocolatey
choco install ollama
```

**macOS:**
```bash
# 下載並安裝 Ollama
# https://ollama.ai/download
# 或使用 Homebrew
brew install ollama
```

**Linux:**
```bash
# 一鍵安裝
curl -fsSL https://ollama.ai/install.sh | sh
```

### 2. 啟動 Ollama 服務

```bash
# 啟動 Ollama 服務 (背景執行)
ollama serve
```

### 3. 下載必要模型

```bash
# 下載 LLM 模型 (文本生成、摘要、翻譯)
ollama pull llama3.1:8b        # 推薦，平衡效能和品質
# 或選擇其他模型:
# ollama pull llama3:8b         # 穩定版本
# ollama pull mistral:7b        # 較小模型，更快速度
# ollama pull qwen2:7b          # 中文優化模型

# 下載 Embedding 模型 (語義搜索、分類)
ollama pull mxbai-embed-large  # 推薦，高品質嵌入向量
# 或選擇其他模型:
# ollama pull nomic-embed-text  # 較小模型
```

### 4. 驗證安裝

```bash
# 檢查已安裝的模型
ollama list

# 測試 LLM 模型
ollama run llama3.1:8b "請用中文介紹文藝復興藝術"

# 測試系統整合
cd /path/to/art-history-database
node scripts/test-ollama-integration.js
```

## 📋 支援的功能

### 🤖 AI 功能對應表

| 原 OpenAI/HF 功能 | Ollama 替代 | 狀態 |
|-------------------|-------------|------|
| GPT-4 文本生成 | llama3.1:8b | ✅ 完全替代 |
| 文本摘要 | 本地模型 + 專用 Prompt | ✅ 完全替代 |
| 多語言翻譯 | 本地模型 + 翻譯 Prompt | ✅ 完全替代 |
| 文本分類 | 本地模型 + 分類邏輯 | ✅ 完全替代 |
| Embedding 向量 | mxbai-embed-large | ✅ 完全替代 |
| 語義搜索 | 本地 Embedding | ✅ 完全替代 |

### 🎨 藝術史專用功能

1. **智能摘要生成**
   - 藝術作品結構化摘要
   - 藝術家生平總結
   - 藝術運動特徵描述

2. **多語言翻譯**
   - 英文 → 繁體中文
   - 英文 → 日文
   - 支援藝術史專業術語

3. **智能分類**
   - 藝術時期分類
   - 藝術風格識別
   - 媒材類型判斷
   - 主題內容分析

4. **語義搜索**
   - 相似作品查找
   - 概念關聯搜索
   - 跨語言搜索

## 🔧 配置說明

### 環境變數設定

```bash
# .env 文件配置
USE_OLLAMA=true                              # 啟用 Ollama
OLLAMA_BASE_URL=http://localhost:11434       # Ollama 服務位址
OLLAMA_DEFAULT_MODEL=llama3.1:8b            # 預設 LLM 模型
OLLAMA_EMBEDDING_MODEL=mxbai-embed-large    # 預設嵌入模型
OLLAMA_TIMEOUT=120000                       # 請求超時 (2分鐘)
```

### 推薦模型配置

**高效能配置** (16GB+ RAM):
```bash
OLLAMA_DEFAULT_MODEL=llama3.1:8b
OLLAMA_EMBEDDING_MODEL=mxbai-embed-large
```

**標準配置** (8-16GB RAM):
```bash
OLLAMA_DEFAULT_MODEL=llama3:8b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

**輕量級配置** (<8GB RAM):
```bash
OLLAMA_DEFAULT_MODEL=mistral:7b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

## 🧪 測試和驗證

### 執行整合測試
```bash
# 完整測試套件
node scripts/test-ollama-integration.js

# 測試特定功能
node -e "
const { ollamaService } = require('./src/services/ollamaService');
ollamaService.generateText('測試中文生成', {maxTokens: 100})
  .then(result => console.log('✅ 測試成功:', result.text))
  .catch(error => console.error('❌ 測試失敗:', error.message));
"
```

### 效能基準測試

**文本生成速度:**
- 目標: >10 tokens/秒
- 實測: 15-50 tokens/秒 (取決於硬體)

**嵌入向量生成:**
- 目標: >5 文本/秒
- 實測: 10-30 文本/秒

**記憶體使用:**
- LLM 模型: 4-8GB
- Embedding 模型: 1-2GB
- 系統開銷: <500MB

## 🚀 使用範例

### 1. 摘要翻譯 Agent

```javascript
const OllamaSummarizationAgent = require('./agents/summarization-translation/ollamaAgent');

const agent = new OllamaSummarizationAgent();
await agent.initialize();

// 開始處理
const results = await agent.startProcessing({
  targetLanguages: ['zh-TW', 'ja'],
  generateSummaries: true,
  generateTranslations: true,
  culturalAdaptation: true
});
```

### 2. 分類 Agent

```javascript
const OllamaClassificationAgent = require('./agents/classification/ollamaAgent');

const agent = new OllamaClassificationAgent();
await agent.initialize();

// 開始分類
const results = await agent.startClassification({
  outputFormat: 'detailed',
  enableCaching: true
});
```

### 3. 直接使用 Ollama 服務

```javascript
const { ollamaService } = require('./src/services/ollamaService');

// 藝術史摘要
const summary = await ollamaService.generateArtSummary({
  title: 'Mona Lisa',
  artist: 'Leonardo da Vinci',
  period: 'Renaissance'
}, 'artwork');

// 翻譯
const translation = await ollamaService.translateArtText(
  'Renaissance art is characterized by realism',
  'en',
  'zh-TW'
);

// 分類
const classification = await ollamaService.classifyArtwork({
  title: 'The Starry Night',
  artist: 'Vincent van Gogh',
  description: 'Post-impressionist painting'
});
```

## 📊 效能最佳化

### 1. 硬體建議

**最低需求:**
- CPU: 4 核心
- RAM: 8GB
- 硬碟: 10GB 可用空間

**推薦配置:**
- CPU: 8+ 核心
- RAM: 16GB+
- GPU: NVIDIA GPU (支援 CUDA)
- 硬碟: SSD, 20GB+ 可用空間

### 2. 效能調優

```bash
# GPU 加速 (如果有 NVIDIA GPU)
# Ollama 會自動偵測並使用 GPU

# 增加並行處理
export OLLAMA_MAX_LOADED_MODELS=2
export OLLAMA_NUM_PARALLEL=4

# 記憶體最佳化
export OLLAMA_FLASH_ATTENTION=1
```

### 3. 批次處理設定

```javascript
// 在 Agent 中調整批次大小
const agent = new OllamaSummarizationAgent();
agent.config.batchSize = 5;  // 減少批次大小以節省記憶體
```

## 🔄 降級和故障恢復

### 自動降級機制

系統內建多層降級機制：

1. **Ollama → 規則式處理**
   - 當 Ollama 不可用時，自動切換到規則式分類
   - 基於關鍵字匹配和既定邏輯

2. **快取機制**
   - 自動快取處理結果
   - 避免重複計算

3. **錯誤恢復**
   - 自動重試失敗請求
   - 記錄錯誤並繼續處理

### 手動切換到 OpenAI

如需暫時使用 OpenAI API：

```bash
# 在 .env 中設定
USE_OLLAMA=false
OPENAI_API_KEY=your_actual_api_key
```

## 🛠️ 疑難排解

### 常見問題

**Q: Ollama 服務連接失敗**
```bash
# 檢查服務狀態
ollama list

# 重新啟動服務
pkill ollama
ollama serve
```

**Q: 模型載入失敗**
```bash
# 重新下載模型
ollama rm llama3.1:8b
ollama pull llama3.1:8b
```

**Q: 記憶體不足**
```bash
# 使用較小模型
ollama pull mistral:7b
# 更新 .env
OLLAMA_DEFAULT_MODEL=mistral:7b
```

**Q: 生成速度太慢**
```bash
# 檢查 GPU 支援
nvidia-smi  # (如果有 NVIDIA GPU)

# 調整模型大小
OLLAMA_DEFAULT_MODEL=llama3:8b  # 或更小的模型
```

### 日誌檢查

```bash
# 檢查 Ollama 日誌
ollama logs

# 檢查應用程式日誌
tail -f logs/app.log | grep -i ollama
```

## 📈 監控和分析

### 整合測試報告

```bash
# 執行完整測試並生成報告
node scripts/test-ollama-integration.js > ollama_test_report.txt
```

### 效能監控

```javascript
// 獲取 Ollama 統計
const stats = await ollamaService.getModelStats();
console.log('Ollama 狀態:', stats);
```

### API 端點

系統提供監控端點：

```bash
# 檢查 Ollama 狀態
curl http://localhost:3000/api/ollama/status

# 獲取效能統計
curl http://localhost:3000/api/ollama/stats
```

## 🎯 下一步

1. **模型調優** - 根據您的數據微調模型
2. **效能最佳化** - 調整硬體配置和參數
3. **功能擴展** - 新增更多藝術史專用功能
4. **監控完善** - 建立完整的效能監控系統

## 📚 參考資源

- [Ollama 官方文檔](https://ollama.ai/docs)
- [支援的模型列表](https://ollama.ai/library)
- [效能調優指南](https://github.com/ollama/ollama/blob/main/docs/performance.md)

---

**🎉 恭喜！您已成功設定 Ollama 本地 AI 模型系統。現在可以享受隱私保護、零成本的 AI 功能了！**