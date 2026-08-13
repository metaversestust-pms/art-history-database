# 📚 OpenWebUI RAG+LLM組合匯入機制完整說明

**文件日期**: 2025-11-04
**系統版本**: v5.0
**檢查狀態**: ✅ 已完成全面檢查

---

## 🎯 執行摘要

經過全面檢查，你的藝術史OpenWebUI系統使用**兩種互補的機制**來實現RAG+LLM組合：

1. **OpenWebUI Function機制** ⭐主要方式
2. **Ollama Modelfile機制** (輔助方式)

---

## 📋 目錄

1. [主要匯入機制](#主要匯入機制openwebui-function)
2. [輔助匯入機制](#輔助匯入機制ollama-modelfile)
3. [當前系統配置](#當前系統配置)
4. [新增模型的正確方式](#新增模型的正確方式)
5. [常見問題解答](#常見問題解答)

---

## 主要匯入機制：OpenWebUI Function

### 🌟 這是你目前主要使用的方式

#### 原理說明

OpenWebUI Function是一個**Python函數**，它作為**中介層**運作：

```
用戶在OpenWebUI選擇模型
         ↓
Function解析模型名稱
         ↓
Function調用RAG服務器 (8010)
         ↓
RAG服務器查詢資料庫
         ↓
Function格式化結果返回給用戶
```

#### 核心檔案

**當前使用版本**: `enhanced_openwebui_rag_function_v4.py`
**最新版本**: `enhanced_openwebui_rag_function_v5.py` (剛創建)

#### Function的關鍵部分

```python
# 1. 定義LLM模型
self.llm_models = {
    "gpt-oss:20b": {...},
    "deepseek-r1:8b": {...},
    "llama3.1:8b": {...},
    # v5.0新增:
    "qwen3:30b": {...},
    "deepseek-r1:32b": {...},
    "llama3.1:70b": {...},
}

# 2. 定義RAG策略
self.rag_strategies = {
    "enhanced_rag": {...},
    "vector_only": {...},
    "graph_only": {...},
    # ... 共8種
}

# 3. 自動生成組合
for model_id in self.llm_models:
    for strategy_id in self.rag_strategies:
        combo_id = f"{model_id}-{strategy_id}"
        self.model_combinations[combo_id] = {...}
```

#### 組合如何顯示在OpenWebUI

當用戶點擊左上角模型選擇器時，看到的組合（如`llama3-1-8b-enhanced_rag`）是由Function**動態生成**的，而不是預先在Ollama中創建的模型。

#### Function如何工作

1. **用戶選擇**: `llama3-1-70b-enhanced_rag`
2. **Function解析**:
   - LLM: `llama3.1:70b`
   - RAG策略: `enhanced_rag`
3. **Function調用RAG服務器**:
   ```python
   POST http://localhost:8010/query
   {
       "query": "達文西的作品",
       "strategy": "enhanced_rag",
       "base_model": "llama3.1:70b"
   }
   ```
4. **RAG服務器返回結果**
5. **Function格式化並返回給用戶**

### ✅ 優點

- ✅ **靈活**: 修改Function即可新增組合，無需重啟服務
- ✅ **集中管理**: 所有邏輯在一個Python檔案中
- ✅ **動態**: 可以根據服務器可用性動態調整
- ✅ **擴展性強**: 易於新增模型和策略

### ⚠️ 更新方式

**必須手動在OpenWebUI界面更新**:

1. 訪問 http://localhost:8080
2. 左側選單 → **Workspace** → **Functions**
3. 找到 "藝術史RAG+LLM完整智能組合系統"
4. 點擊**編輯**
5. 複製新版Function的全部內容
6. 貼上並**保存**

**這就是為什麼你需要手動更新到v5.0的原因！**

---

## 輔助匯入機制：Ollama Modelfile

### 📦 這是輔助/備用方式

#### 原理說明

Ollama Modelfile機制是通過**創建新的Ollama模型**來實現組合。這些模型實際上是基礎模型的"包裝"，帶有特定的提示詞和參數。

#### 相關腳本

你的系統中有多個創建模型的腳本：

1. **create_rag_models.py** - 基礎版本
2. **create_virtual_models.py** - 虛擬模型版本
3. **create_advanced_rag_models.py** - 進階版本
4. **create_full_rag_models.sh** - Shell腳本版本
5. **create_extended_rag_models.py** - v5.0新版本

#### Modelfile機制的工作流程

```bash
# 1. 創建Modelfile
FROM llama3.1:8b
SYSTEM "你是藝術史專家..."
PARAMETER temperature 0.1

# 2. 通過Ollama API創建新模型
ollama create llama31-vector-rag -f Modelfile

# 3. 新模型出現在Ollama模型列表中
ollama list
# 會顯示: llama31-vector-rag
```

#### 檢查已創建的模型

```bash
curl -s http://localhost:11434/api/tags | python3 -m json.tool | grep "name"
```

**當前結果**:
```json
"name": "llama3.1:70b",
"name": "qwen3:30b",
"name": "deepseek-r1:32b",
"name": "gpt-oss:20b",
"name": "deepseek-r1:8b",
"name": "llama3-graph-rag:latest",  ← 唯一一個通過Modelfile創建的
"name": "llama3.1:8b",
```

### 📊 觀察結果

**只有`llama3-graph-rag`是通過Modelfile創建的！**

其他都是：
- 基礎模型（從Ollama Hub下載）
- 或嵌入模型（nomic-embed-text, bge-m3）

這證明了**你主要使用Function機制**！

### ✅ 優點

- ✅ 模型持久化在Ollama中
- ✅ 可以獨立於OpenWebUI使用
- ✅ 模型參數預先配置

### ❌ 缺點

- ❌ 創建72個模型會佔用大量存儲
- ❌ 修改需要重新創建所有模型
- ❌ 管理複雜
- ❌ 不夠靈活

---

## 當前系統配置

### ✅ 已確認的配置

#### 1. OpenWebUI Function (主要)

**檔案**: `enhanced_openwebui_rag_function_v4.py`

**特點**:
- 定義5種LLM模型
- 定義8種RAG策略
- 生成40種組合
- 通過多資料庫RAG服務器(8010)路由查詢

#### 2. RAG服務器

**多資料庫RAG服務器** (主要使用):
- 檔案: `multi-database-rag-server.js`
- 端口: 8010
- 支援8種策略
- 整合Neo4j + ChromaDB

**Neo4j Graph RAG服務器** (圖譜專用):
- 檔案: `neo4j_graph_rag_server.py`
- 端口: 8008
- 專門處理圖譜查詢

#### 3. Ollama基礎模型

**已安裝的LLM模型** (9個):
```
✅ llama3.1:70b      - 剛下載
✅ qwen3:30b         - 剛下載
✅ deepseek-r1:32b   - 剛下載
✅ gpt-oss:20b
✅ deepseek-r1:8b
✅ llama3.1:8b
✅ qwen2.5:7b
✅ qwen3:8b
✅ gemma2:2b
```

**嵌入模型** (2個):
```
✅ nomic-embed-text
✅ bge-m3
```

#### 4. 數據庫

- **Neo4j**: 4,946節點, 5,616關係
- **ChromaDB**: 1,441向量, 95.5%中文覆蓋

---

## 新增模型的正確方式

### 🎯 推薦方式：更新OpenWebUI Function

**這是最簡單、最有效的方式！**

#### 步驟1: 確保基礎模型已下載

✅ 你已經完成了！
```bash
ollama pull llama3.1:70b
ollama pull qwen3:30b
ollama pull deepseek-r1:32b
```

#### 步驟2: 更新Function到v5.0

1. 訪問 http://localhost:8080
2. Workspace → Functions
3. 編輯 "藝術史RAG+LLM完整智能組合系統"
4. 複製 `enhanced_openwebui_rag_function_v5.py` 的全部內容
5. 貼上並保存

**就這樣！不需要其他操作！**

#### 步驟3: 驗證

1. 重新整理頁面
2. 點擊左上角模型選擇器
3. 搜索 `llama3-1-70b` 或 `qwen3-30b`
4. 應該看到新組合！

### 🔧 備用方式：創建Ollama模型（可選）

**只有在你想要獨立使用這些組合時才需要**

```bash
# 進入專案目錄
cd /mnt/c/Users/ssking1999/Desktop/藝術史資料庫/art-history-database

# 運行創建腳本
python3 create_extended_rag_models.py
```

**注意**: 這會創建72個模型，需要：
- 大量儲存空間 (~200GB+)
- 較長時間 (~30-60分鐘)
- 對於Function機制來說**並不必要**

---

## 兩種機制的比較

| 特性 | OpenWebUI Function | Ollama Modelfile |
|------|-------------------|------------------|
| **你主要使用** | ✅ 是 | ❌ 否 |
| **更新方式** | 修改Function並在UI更新 | 重新創建所有模型 |
| **存儲需求** | 很小 (~100KB Python檔) | 很大 (~200GB+) |
| **靈活性** | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| **新增模型** | 秒級 | 30-60分鐘 |
| **管理複雜度** | 低 (一個檔案) | 高 (72個模型) |
| **推薦程度** | ⭐⭐⭐⭐⭐ | ⭐⭐ (僅備用) |

---

## 常見問題解答

### Q1: 我需要運行`create_extended_rag_models.py`嗎？

**A**: **不需要！** 只要更新Function到v5.0就夠了。

除非你想：
- 在OpenWebUI外獨立使用這些組合
- 有充足的存儲空間 (200GB+)
- 不介意等待30-60分鐘

### Q2: 為什麼我在模型選擇器中看不到新模型？

**A**: 可能的原因：
1. ❌ Function還沒更新到v5.0
2. ❌ 頁面沒有重新整理
3. ❌ 瀏覽器緩存

**解決方案**:
```
1. 確認Function已更新
2. 按Ctrl+F5強制重新整理
3. 清除瀏覽器緩存
```

### Q3: Function和Modelfile可以同時使用嗎？

**A**: 可以，但**不推薦**。

- Function會優先處理匹配的模型名稱
- 如果Function和Modelfile都定義了相同名稱，Function會接管
- 容易造成混淆

**建議**: 統一使用Function機制。

### Q4: 如何確認我使用的是哪種機制？

**A**: 檢查方法：

```bash
# 1. 檢查Ollama中的模型
curl -s http://localhost:11434/api/tags | grep "name"

# 2. 如果只看到基礎模型（如llama3.1:70b）
#    → 使用Function機制

# 3. 如果看到大量組合模型（如llama31-vector-rag）
#    → 使用Modelfile機制
```

**你的情況**: 只有基礎模型 + 一個llama3-graph-rag
**結論**: **主要使用Function機制** ✅

### Q5: 更新Function後需要重啟服務嗎？

**A**: **不需要！**

OpenWebUI Function是動態載入的：
- 在UI中保存後立即生效
- 無需重啟任何服務
- 只需重新整理頁面

### Q6: Function在哪裡儲存？

**A**: Function儲存在**OpenWebUI的資料庫**中。

**位置**: `openwebui_data` Docker volume

**檔案形式的Function** (`enhanced_openwebui_rag_function_v5.py`) 只是：
- 原始碼備份
- 方便編輯和版本控制
- 需要手動複製到UI中才會生效

### Q7: 我可以混合使用多個Function嗎？

**A**: 可以，OpenWebUI支援多個Function：

- 每個Function處理不同的模型前綴
- 或提供不同的功能
- 但對於RAG組合，**一個Function就夠了**

---

## 📊 系統架構圖（完整版）

```
┌─────────────────────────────────────────────────────────────┐
│                  用戶瀏覽器 (localhost:8080)                 │
│              OpenWebUI - 選擇模型組合                        │
│                                                               │
│  示例: llama3-1-70b-enhanced_rag                             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│        enhanced_openwebui_rag_function_v5.py                 │
│                   (OpenWebUI Function)                        │
│                                                               │
│  1. 解析模型名稱:                                            │
│     - LLM: llama3.1:70b                                      │
│     - RAG策略: enhanced_rag                                  │
│                                                               │
│  2. 選擇服務器: 多資料庫RAG服務器 (8010)                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│           Multi-Database RAG Server (Port 8010)              │
│              multi-database-rag-server.js                    │
│                                                               │
│  根據策略決定查詢哪個資料庫                                  │
└──────┬────────────────────────────────────────┬─────────────┘
       │                                        │
       ▼                                        ▼
┌──────────────┐                        ┌──────────────┐
│   Neo4j      │                        │  ChromaDB    │
│   (7474)     │                        │   (8001)     │
│              │                        │              │
│ 4,946 節點   │                        │ 1,441 向量   │
│ 5,616 關係   │                        │ 95.5% 中文   │
└──────────────┘                        └──────────────┘
       │                                        │
       └────────────────┬───────────────────────┘
                        │
                        ▼ (檢索結果返回)
┌─────────────────────────────────────────────────────────────┐
│                    Function 格式化結果                        │
│                                                               │
│  - 添加來源標記                                               │
│  - 格式化參考資料                                             │
│  - 顯示執行信息                                               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Ollama (Port 11434)                             │
│                                                               │
│  使用基礎LLM模型生成答案:                                     │
│  - llama3.1:70b                                              │
│  - 基於檢索到的資料                                           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼ (最終答案)
┌─────────────────────────────────────────────────────────────┐
│               返回給用戶的完整回答                            │
│                                                               │
│  內容:                                                        │
│  - LLM生成的答案                                              │
│  - 📊 執行信息 (模型、策略、資料庫)                          │
│  - 📚 參考資料 (含來源追蹤)                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 結論

### 你的系統使用的機制

**✅ 主要機制**: OpenWebUI Function (`enhanced_openwebui_rag_function_v4.py`)
**📦 輔助機制**: Ollama Modelfile (僅`llama3-graph-rag`使用)

### 新增模型的正確做法

**只需要做這一件事**:

1. ✅ 確保基礎模型已下載（你已完成）
2. ✅ 更新Function到v5.0（5分鐘）

**不需要做**:
- ❌ 運行`create_extended_rag_models.py`
- ❌ 重啟任何服務
- ❌ 修改Docker配置

### 立即行動

```
1. 訪問 http://localhost:8080
2. Workspace → Functions
3. 編輯 Function
4. 複製貼上 enhanced_openwebui_rag_function_v5.py
5. 保存
6. 重新整理頁面
7. 完成！開始使用72種組合！
```

---

**文件**: OpenWebUI_RAG組合匯入機制說明.md
**日期**: 2025-11-04
**版本**: 1.0
**狀態**: ✅ 檢查完成
